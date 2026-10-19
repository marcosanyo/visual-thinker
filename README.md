# visual-thinker

An [Agent Skill](https://agentskills.io) that lets a coding agent **draw a diagram in the middle of an explanation**.
Ask Claude Code (or Codex, or any agent that reads `SKILL.md`) how a system fits together, and it answers with a
picture first, then explains it region by region.

日本語: [README.ja.md](README.ja.md)

| Architecture | State machine | Mental model |
|---|---|---|
| ![Architecture example](docs/gallery/architecture.png) | ![State machine example](docs/gallery/state-machine.png) | ![Mental model example](docs/gallery/mental-model.png) |

*Generated with this skill (Vertex AI, `gemini-nano-banana-2.1`) from recipes A, C and D in
[prompt_recipes.md](skills/visual-thinker/references/prompt_recipes.md), the first two with
`--style "white background, flat vector, large readable text"`.*

## Why

Many developers understand a system much faster from a picture than from paragraphs. Agents already explain
architecture, request flows and state machines all day, but in text, or in Mermaid that only covers boxes and
arrows. This skill gives the agent:

- **When to draw**: the skill description tells the agent to draw when you ask ("draw it", "図で説明して") or when an
  explanation would be hard to follow as text.
- **What to ask for**: six presets (`architecture`, `flow`, `state-machine`, `mental-model`, `ui-wireframe`,
  `generic`) and prompt rules for diagrams: layout first, exact short labels, directed arrows, color by meaning.
- **How to answer**: picture first, bullets that follow the picture, a check of the image for misspelled labels or
  reversed arrows, and Mermaid or code next to it when exact structure matters.
- **A small generator**: one Python file, standard library only, no package to install.

## Install

### Claude Code (plugin)

```text
/plugin marketplace add marcosanyo/visual-thinker
/plugin install visual-thinker@visual-thinker
```

### Claude Code, Codex and other agents (copy the skill)

```bash
git clone https://github.com/marcosanyo/visual-thinker
cp -r visual-thinker/skills/visual-thinker ~/.claude/skills/      # Claude Code, all projects
cp -r visual-thinker/skills/visual-thinker .claude/skills/        # Claude Code, this project only
cp -r visual-thinker/skills/visual-thinker ~/.codex/skills/       # Codex
```

For other agents, copy `skills/visual-thinker/` to wherever the agent loads skills from.

## Configure an image provider

Set the credentials for **one** provider (in your shell, or in a `.env` file in the directory you run from):

| Provider | Credentials | Model | Tested by the author |
|---|---|---|---|
| `vertex` (Google Vertex AI) | `GOOGLE_CLOUD_PROJECT`, plus `gcloud auth login` (or `VERTEX_ACCESS_TOKEN`) | default `gemini-nano-banana-2.1` | yes |
| `gemini` (Gemini Developer API) | `GEMINI_API_KEY` | `--model` required | no |
| `openai` (OpenAI Images API) | `OPENAI_API_KEY` | `--model` required | no |
| `openrouter` | `OPENROUTER_API_KEY` | `--model` required | no |

If more than one is set, choose with `--provider` or `VISUAL_THINKER_PROVIDER`. `VISUAL_THINKER_MODEL` sets the
model, and `VERTEX_AI_LOCATION` the Vertex region (default `global`).

## Use

Just ask: "Explain how auth works in this repo, with a diagram." The agent runs the generator for you. You can run
it yourself too:

```bash
python3 skills/visual-thinker/scripts/generate_diagram.py \
  --type flow \
  --prompt "Numbered steps 1 to 3, left to right: 'Browser' -> 'API Gateway' -> 'Lambda'. Step labels 'HTTPS', 'invoke'." \
  --style "white background, large readable text" \
  --open
```

| Option | Meaning |
|---|---|
| `-p, --prompt` | what to draw: parts, connections, exact labels (required) |
| `-t, --type` | preset: `architecture` (default), `flow`, `state-machine`, `mental-model`, `ui-wireframe`, `generic` |
| `--provider`, `-m, --model` | see the table above |
| `-a, --aspect` | aspect ratio, default `16:9` |
| `--style` | extra style words |
| `-o, --output` | output file (default `.visual-thinker/diagram_<type>_<time>.png`) |
| `--open` | open in the system viewer (macOS, Windows, or Linux with `xdg-open`) |
| `--dry-run` | print the full prompt without calling an API |

### Errors are shown, never hidden

One run uses one provider and one model. If the call fails (missing credentials, 403, 404 model not found, quota),
the script prints the provider's error and exits with status 1. It does not switch to another model or provider,
and it never draws a placeholder. The skill tells the agent to show you that error as is.

## Limits

Image models can misspell a label, reverse an arrow or add a box that isn't there. Use these pictures for intuition,
check them before you rely on them, and use Mermaid, a table or code for anything that must be exact (wiring,
protocol order, field names). The skill tells the agent to do the same.

## Layout

```text
.claude-plugin/
  plugin.json            # Claude Code plugin manifest
  marketplace.json       # lets the repo itself be added as a marketplace
skills/visual-thinker/
  SKILL.md               # what the agent reads: when to draw, how to prompt, how to answer
  scripts/generate_diagram.py
  references/prompt_recipes.md
docs/gallery/            # the images above
README.ja.md             # Japanese README
```

## Origin

Started during the Amazon Developer Hackathon (2026), where it was used to sketch the architecture of FireSense
Kids, a Fire TV project, while it was being designed.

## License

[MIT](LICENSE)
