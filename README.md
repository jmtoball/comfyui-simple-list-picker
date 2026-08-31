# Simple List Picker

A ComfyUI node that takes a list and an index and returns the item at that index.

That is the whole node. It exists because the obvious way to write it is subtly
wrong, and the wrong version fails in a way that looks like the index being
ignored.

## Install

```bash
git clone https://github.com/jmtoball/comfyui-simple-list-picker.git
```

into `ComfyUI/custom_nodes/` and restart. No dependencies.

## Use

```
Create List  ──list──▶  Simple List Picker  ──item──▶  (anything)
Primitive Int ─index──▶
```

| input | |
|---|---|
| `items` | Any list output — `Create List`, or anything with `OUTPUT_IS_LIST` |
| `index` | Negative counts from the end, as in Python |
| `mode` | `wrap` (default), `clamp`, or `error` when the index is out of range |

| output | |
|---|---|
| `item` | The value at that index, of whatever type went in |
| `resolved_index` | Where the index actually landed after wrap/clamp |
| `count` | How many items the list held |

### One item per queued job

The `index` widget carries `control_after_generate`. Set it to **`increment`**
and it advances once per queued run, exactly as a seed does:

1. Put your prompts in a `Create List`.
2. Wire `Simple List Picker` between it and your text input.
3. Set `index` to `0` and its control to `increment`.
4. Queue with a batch count of N.

Each job takes the next prompt. With `mode: wrap` you can queue more jobs than
you have prompts and it cycles.

Two things worth knowing: the index is a counter, not a queue, so nothing is
consumed and re-running a job repeats its prompt; and the counter keeps climbing
between sessions, so reset it by hand when you want to start over.

## Why this needs to be its own node

ComfyUI has two different things that both get called a list:

- a **list output** — a socket flagged `OUTPUT_IS_LIST`, which is what
  `Create List` produces. Downstream nodes never receive the list. The executor
  runs them **once per item** and collects the results.
- a **Python list received whole**, which only happens when the receiving node
  declares `INPUT_IS_LIST = True`.

A generic "index into any input" node that does not declare `INPUT_IS_LIST` is
therefore invoked once per element and returns each of them in turn. From the
graph it looks as though the index is being ignored — the node is working
exactly as written, on one item at a time, having never seen a list.

This node declares `INPUT_IS_LIST`, so it receives every item and returns one.
The consequence is that *all* its inputs arrive wrapped, `index` included: a
widget set to `3` shows up as `[3]`. Unwrapping those is the other half of the
job, and getting it wrong turns the index into a list and the arithmetic into
something else.

## Development

```bash
pip install pytest ruff
ruff check .
pytest tests
```

CI runs both on Python 3.10, 3.11 and 3.12.

## License

MIT
