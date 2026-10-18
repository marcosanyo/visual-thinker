# Prompt recipes for technical diagrams

The script adds a preset (layout and style for the chosen `--type`) in front of your prompt. Your prompt is the
content: what is in the picture, where, and what it says. These rules and recipes work across image models.

## Rules

1. **Layout first.** Say where things go: "three columns, left to right", "top: clients, middle: services,
   bottom: storage", "numbered steps along a horizontal line".
2. **Exact, short labels in quotes.** `'API Gateway'`, `'Auth'`, `'Redis'`. Put the long explanation in your reply,
   not in the image. Fewer labels means fewer misspellings.
3. **Every arrow has a direction and, if needed, a label.** "An arrow FROM 'Worker' TO 'S3' labeled 'upload'."
   Models often reverse or duplicate arrows; say "no other arrows" when it matters.
4. **Color by meaning, and say it.** For example blue = services, amber = queues and events, green = storage and
   success, red = security boundaries and errors, gray = neutral connections.
5. **Style in a few words** with `--style`: "white background, flat vector, large readable text" for documents,
   "dark slate background, high contrast" for slides.
6. **Check, then iterate.** If a label is wrong or an arrow is reversed, repeat the prompt with one explicit
   correction ("Important: the arrow goes FROM 'Client' TO 'Gateway'").

## Recipe A: cloud architecture (`--type architecture`)

```text
Three columns, left to right.
Left: 'Web app' and 'Mobile app'.
Middle, inside a box labeled 'AWS': 'API Gateway' routing to 'Auth', 'Catalog' and 'Payment'.
Right: 'PostgreSQL' and 'Redis'.
Arrows: from both apps to 'API Gateway' labeled 'HTTPS'; from 'Catalog' to 'Redis' labeled 'cache';
from 'Auth' and 'Payment' to 'PostgreSQL'. No other arrows.
```

## Recipe B: event pipeline (`--type flow`)

```text
Numbered steps 1 to 5 from left to right:
1 'Producer' publishes to 'orders topic';
2 the topic fans out to three 'Worker' boxes;
3 a worker processes the order;
4 on failure, a red branch down to 'Dead-letter queue';
5 results go to 'Search index' and 'S3'.
```

## Recipe C: job lifecycle (`--type state-machine`)

```text
States: 'Queued' -> 'Running' -> 'Done'.
From 'Running', a transition 'error (attempt < 3)' to 'Retrying', and from 'Retrying' back to 'Running' labeled 'backoff'.
From 'Running', a transition 'error (attempt = 3)' to 'Dead letter' in red.
```

## Recipe D: race condition (`--type mental-model`)

```text
Split picture. Left, titled 'Data race': two runners, 'Thread A' in blue and 'Thread B' in orange, grabbing the same
box 'balance' at once; the box cracks. Right, titled 'With a lock': a gate labeled 'mutex' lets one runner in while
the other waits in line.
```
