---
name: visual-thinker
description: Draws a technical diagram (architecture, flow, state machine, mental model, UI wireframe) with an image model and puts it at the top of the explanation. Use when the user asks for a diagram or a picture ("draw it", "図で説明して", "図解して"), says they think visually, or when an explanation of a system, data flow, lifecycle or abstract mechanism would be hard to follow as text alone.
license: MIT
---

# Visual Thinker

Some people understand a system much faster from a picture than from paragraphs. This skill lets you draw one in
the middle of an explanation: you describe the diagram, a script sends it to an image model, and you show the image
first, then explain it region by region.

## 1. Decide what to draw

Pick one preset with `--type`:

| Preset | For |
|---|---|
| `architecture` | components, services, data stores and how they connect |
| `flow` | a sequence: request lifecycles, pipelines, handshakes, numbered steps |
| `state-machine` | states and the events, guards or timeouts that move between them |
| `mental-model` | an abstract mechanism shown as a spatial metaphor (race conditions, consensus, caches) |
| `ui-wireframe` | screen regions, component hierarchy, screen-to-screen flow |
| `generic` | anything else |

Write the prompt as a short spec, not prose: the layout direction (left to right, top to bottom), each box with its
**exact label**, each arrow with its label, and grouping (which boxes sit inside which boundary). Image models misspell
and invent text, so keep labels few and short. See `references/prompt_recipes.md` for worked examples.

## 2. Generate

Run the script in this skill's directory (Python 3.9+, standard library only) from the user's project root:

```bash
python3 <this skill's directory>/scripts/generate_diagram.py \
  --type architecture \
  --prompt "Left: 'Browser'. Middle: 'API Gateway' -> 'Lambda'. Right: 'DynamoDB'. Arrows labeled 'HTTPS' and 'query'." \
  --open
```

- The provider comes from `--provider` or `VISUAL_THINKER_PROVIDER`, else the only one whose credentials are set.
  `vertex` defaults to the model `gemini-nano-banana-2.1`; the other providers need `--model`.
- Other options: `--aspect 16:9` (default), `--style "white background, large text"`, `--output path.png`,
  `--dry-run` (print the full prompt, no API call).
- The script prints `File:` and a `Markdown:` line. It writes to `.visual-thinker/` in the current directory unless
  `--output` is given.
- **If it fails, it exits with the provider's error and does not try another provider or model.** Show the user
  the error as is (missing credentials, 403, 404 model not found, quota). Do not retry with a different model
  unless the user asks you to, and do not draw a substitute yourself.

## 3. Answer, picture first

1. Put the image at the top of the reply (the `Markdown:` line, or the file path in a terminal; `--open` also opens
   it in the system viewer).
2. Then explain in short bullets that follow the picture's regions: left to right, or step 1, 2, 3.
3. **Check the image before you rely on it.** Generated diagrams can misspell labels, reverse an arrow or add a box
   that isn't there. Look at it; if something is wrong, say so in the reply or generate again with a clearer prompt.
4. When exact structure matters (wiring, protocol order, field names), add a Mermaid diagram or a code block next to
   the picture: the image gives the intuition, the text gives the precise facts.
