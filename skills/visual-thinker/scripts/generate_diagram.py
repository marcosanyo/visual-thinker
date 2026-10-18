#!/usr/bin/env python3
"""Generate a technical diagram with an image model, for an agent explaining something to a visual thinker.

Standard library only (Python 3.9+). One provider and one model per run: if the call fails, the script exits with
the provider's error. It never switches to another provider or model, and never draws a placeholder.

Providers
  vertex      Google Vertex AI, generateContent. Needs GOOGLE_CLOUD_PROJECT, and an access token from
              VERTEX_ACCESS_TOKEN or `gcloud auth print-access-token`. Default model: gemini-nano-banana-2.1.
  gemini      Gemini Developer API, generateContent. Needs GEMINI_API_KEY and --model (not verified by the author).
  openai      OpenAI Images API. Needs OPENAI_API_KEY and --model (not verified by the author).
  openrouter  OpenRouter chat completions with image output. Needs OPENROUTER_API_KEY and --model (not verified).

Examples
  generate_diagram.py --type architecture --prompt "Next.js app -> API Gateway -> Lambda -> DynamoDB" --open
  generate_diagram.py --provider openai --model <image-model-id> --type flow --prompt "OAuth code flow"
  generate_diagram.py --type state-machine --prompt "job: queued -> running -> done | retry | dead-letter" --dry-run
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

PRESETS = {
    "architecture": (
        "Professional software architecture diagram, flat vector infographic. Clear modular blocks for services, "
        "data stores and queues, grouped by boundary (client, cloud, data). Directional connector lines with short "
        "protocol labels (HTTPS, gRPC, WebSocket). Generous spacing, clean sans-serif labels, restrained palette."
    ),
    "flow": (
        "End-to-end sequence and data-flow diagram, clean minimalist technical illustration. Numbered steps (1, 2, 3...) "
        "showing how data moves between the parts, clear directional arrows, error branches drawn as a separate fork."
    ),
    "state-machine": (
        "Finite state machine diagram, clean modern infographic. Rounded state nodes with color-coded status, labeled "
        "transition arrows naming the event, guard or timeout that triggers each transition."
    ),
    "mental-model": (
        "Intuitive mental-model illustration of an abstract mechanism. Explains it through spatial relationships, layers "
        "and one clear visual metaphor, isometric 2.5D, clean vector style, minimal clutter."
    ),
    "ui-wireframe": (
        "Clean UI wireframe: screen regions, component hierarchy, navigation, content cards and interaction states, "
        "drawn as a neutral blueprint."
    ),
    "generic": (
        "High-clarity technical diagram for software engineers. Clean vector style, organized layout, crisp labels, "
        "arrows showing relationships and flows."
    ),
}
LEGIBILITY = "Use only short labels, spelled exactly as given in the concept; no other text, no logos."

DEFAULT_MODELS = {"vertex": "gemini-nano-banana-2.1"}
CREDENTIALS = {
    "vertex": "GOOGLE_CLOUD_PROJECT",
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}
OPENAI_SIZES = {"1:1": "1024x1024", "16:9": "1536x1024", "3:2": "1536x1024", "9:16": "1024x1536", "2:3": "1024x1536"}
TIMEOUT_S = 300


class Failure(Exception):
    """An error to show the user as is, then exit 1."""


def load_dotenv(path: Path) -> None:
    """Read KEY=VALUE lines from ./.env without overriding variables that are already set."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip().removeprefix("export ").strip(), value.strip().strip("'\""))


def build_prompt(concept: str, diagram_type: str, style: str, aspect: str) -> str:
    parts = [PRESETS[diagram_type], LEGIBILITY]
    if style:
        parts.append("Style: " + style)
    parts.append(f"Aspect ratio {aspect}.")
    parts.append("Concept: " + concept)
    return " ".join(parts)


def choose_provider(requested: str) -> str:
    if requested:
        return requested
    configured = [p for p, var in CREDENTIALS.items() if os.environ.get(var)]
    if len(configured) == 1:
        return configured[0]
    if not configured:
        raise Failure(
            "No provider is configured. Set one of: GOOGLE_CLOUD_PROJECT (vertex), GEMINI_API_KEY, OPENAI_API_KEY, "
            "OPENROUTER_API_KEY, or pass --provider."
        )
    raise Failure(f"Several providers are configured ({', '.join(configured)}). Pick one with --provider or VISUAL_THINKER_PROVIDER.")


def require_env(name: str, provider: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise Failure(f"{provider}: set {name}.")
    return value


def post_json(url: str, headers: dict, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise Failure(f"HTTP {e.code} from {url.split('?')[0]}: {e.read().decode(errors='replace')[:800]}") from None
    except urllib.error.URLError as e:
        raise Failure(f"Could not reach {url.split('?')[0]}: {e.reason}") from None


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=TIMEOUT_S) as resp:
        return resp.read()


def image_from_parts(data: dict) -> tuple[bytes, str]:
    """The first inline image of a generateContent response, as (bytes, mime type)."""
    candidates = data.get("candidates") or []
    for part in (candidates[0].get("content", {}).get("parts", []) if candidates else []):
        inline = part.get("inlineData")
        if inline:
            return base64.b64decode(inline["data"]), inline.get("mimeType", "image/png")
    raise Failure("The response has no image: " + json.dumps(data)[:800])


def vertex_token() -> str:
    token = os.environ.get("VERTEX_ACCESS_TOKEN")
    if token:
        return token
    gcloud = shutil.which("gcloud")
    if not gcloud:
        raise Failure("vertex: set VERTEX_ACCESS_TOKEN, or install gcloud and run `gcloud auth login`.")
    result = subprocess.run([gcloud, "auth", "print-access-token"], capture_output=True, text=True)
    if result.returncode != 0:
        raise Failure("vertex: `gcloud auth print-access-token` failed: " + result.stderr.strip())
    return result.stdout.strip()


def generate_content_body(prompt: str, aspect: str) -> dict:
    return {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}},
    }


def call_vertex(prompt: str, model: str, aspect: str) -> tuple[bytes, str]:
    project = require_env("GOOGLE_CLOUD_PROJECT", "vertex")
    location = os.environ.get("VERTEX_AI_LOCATION", "global")
    host = "aiplatform.googleapis.com" if location == "global" else f"{location}-aiplatform.googleapis.com"
    url = f"https://{host}/v1/projects/{project}/locations/{location}/publishers/google/models/{model}:generateContent"
    return image_from_parts(post_json(url, {"Authorization": "Bearer " + vertex_token()}, generate_content_body(prompt, aspect)))


def call_gemini(prompt: str, model: str, aspect: str) -> tuple[bytes, str]:
    key = require_env("GEMINI_API_KEY", "gemini")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    return image_from_parts(post_json(url, {"x-goog-api-key": key}, generate_content_body(prompt, aspect)))


def call_openai(prompt: str, model: str, aspect: str) -> tuple[bytes, str]:
    key = require_env("OPENAI_API_KEY", "openai")
    if aspect not in OPENAI_SIZES:
        raise Failure(f"openai: --aspect must be one of {', '.join(OPENAI_SIZES)}.")
    body = {"model": model, "prompt": prompt, "n": 1, "size": OPENAI_SIZES[aspect]}
    data = post_json("https://api.openai.com/v1/images/generations", {"Authorization": "Bearer " + key}, body)
    item = (data.get("data") or [{}])[0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"]), "image/png"
    if item.get("url"):
        return fetch(item["url"]), "image/png"
    raise Failure("The response has no image: " + json.dumps(data)[:800])


def call_openrouter(prompt: str, model: str, aspect: str) -> tuple[bytes, str]:
    key = require_env("OPENROUTER_API_KEY", "openrouter")
    body = {"model": model, "modalities": ["image", "text"], "messages": [{"role": "user", "content": prompt}]}
    data = post_json("https://openrouter.ai/api/v1/chat/completions", {"Authorization": "Bearer " + key}, body)
    images = ((data.get("choices") or [{}])[0].get("message") or {}).get("images") or []
    url = images[0].get("image_url", {}).get("url", "") if images and isinstance(images[0], dict) else ""
    if url.startswith("data:image/") and ";base64," in url:
        header, b64 = url.split(";base64,", 1)
        return base64.b64decode(b64), header.removeprefix("data:")
    if url.startswith("http"):
        return fetch(url), "image/png"
    raise Failure("The response has no image: " + json.dumps(data)[:800])


CALLS = {"vertex": call_vertex, "gemini": call_gemini, "openai": call_openai, "openrouter": call_openrouter}
EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


def open_in_viewer(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=True)
    elif sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif shutil.which("xdg-open"):
        subprocess.run(["xdg-open", str(path)], check=True)
    else:
        raise Failure(f"--open: no image viewer found (macOS `open`, Windows, or `xdg-open`). The file is at {path}")


def main() -> int:
    load_dotenv(Path.cwd() / ".env")
    ap = argparse.ArgumentParser(description="Generate a technical diagram with an image model.")
    ap.add_argument("-p", "--prompt", required=True, help="What to draw: the parts, how they connect, the exact labels.")
    ap.add_argument("-t", "--type", choices=sorted(PRESETS), default="architecture", help="Diagram preset (default: architecture).")
    ap.add_argument("--provider", choices=sorted(CALLS), default=os.environ.get("VISUAL_THINKER_PROVIDER") or None,
                    help="Image provider. Default: VISUAL_THINKER_PROVIDER, else the only provider with credentials set.")
    ap.add_argument("-m", "--model", default=os.environ.get("VISUAL_THINKER_MODEL") or None,
                    help="Model ID. Required except for vertex (default gemini-nano-banana-2.1).")
    ap.add_argument("-a", "--aspect", default="16:9", help="Aspect ratio, for example 16:9, 4:3, 1:1 (default 16:9).")
    ap.add_argument("--style", default="", help="Extra style instructions, for example 'white background, large text'.")
    ap.add_argument("-o", "--output", help="Output file. Default: .visual-thinker/diagram_<type>_<time>.<ext> in the current directory.")
    ap.add_argument("--open", action="store_true", help="Open the image in the system viewer.")
    ap.add_argument("--dry-run", action="store_true", help="Print the full prompt and exit without calling any API.")
    args = ap.parse_args()

    prompt = build_prompt(args.prompt, args.type, args.style, args.aspect)
    if args.dry_run:
        print(prompt)
        return 0
    try:
        provider = choose_provider(args.provider)
        model = args.model or DEFAULT_MODELS.get(provider)
        if not model:
            raise Failure(f"{provider}: pass --model (or set VISUAL_THINKER_MODEL); this provider has no default model.")
        print(f"[visual-thinker] {provider} / {model} ...", file=sys.stderr)
        data, mime = CALLS[provider](prompt, model, args.aspect)
        if args.output:
            out = Path(args.output)
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = Path.cwd() / ".visual-thinker" / f"diagram_{args.type}_{stamp}{EXTENSIONS.get(mime, '.png')}"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        try:
            shown = out.resolve().relative_to(Path.cwd())
        except ValueError:
            shown = out.resolve()
        print(f"File: {out.resolve()}")
        print(f"Markdown: ![{args.type}]({shown})")
        if args.open:
            open_in_viewer(out.resolve())
        return 0
    except Failure as e:
        print(f"[visual-thinker] error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
