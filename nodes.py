"""Take one item out of a ComfyUI list.

ComfyUI has two things that both get called "a list", and the difference is the
whole reason this node exists:

* a *list output* -- a socket flagged ``OUTPUT_IS_LIST``, which is what the
  built-in ``Create List`` produces. Downstream nodes do not receive the list;
  the executor runs them once per item and collects the results.
* a Python list that a node receives whole, which only happens when that node
  declares ``INPUT_IS_LIST = True``.

Nodes that index "any" input without declaring ``INPUT_IS_LIST`` therefore never
see a list at all -- they get invoked once per element and dutifully return each
one, which looks like the index being ignored. This node declares it, so it
receives every item and returns exactly one.

The index widget carries ``control_after_generate``, so setting it to
``increment`` walks one step per queued job: define the prompts once, queue N
runs, get one prompt each.
"""

from __future__ import annotations

from typing import Any

MODES = ("wrap", "clamp", "error")


class AnyType(str):
    """A type that compares equal to every other, so the socket accepts anything.

    ComfyUI decides whether two sockets may connect by comparing type strings.
    The established idiom for a genuinely generic socket is a string subclass
    whose inequality test is always False.
    """

    def __ne__(self, other: object) -> bool:  # noqa: D105
        return False

    def __eq__(self, other: object) -> bool:  # noqa: D105
        return True

    def __hash__(self) -> int:  # noqa: D105
        return hash(str(self))


ANY = AnyType("*")


def _single(value: Any) -> Any:
    """Unwrap a widget value.

    With ``INPUT_IS_LIST`` every input arrives as a list, including the scalar
    widgets -- ``index`` shows up as ``[3]``. Forgetting this is the classic bug
    in list-aware nodes: the index becomes a list and the arithmetic silently
    does something else.
    """
    if isinstance(value, list):
        return value[0] if value else None
    return value


def resolve_index(index: int, count: int, mode: str) -> int:
    """Where ``index`` actually lands in a list of ``count`` items.

    Negative indices count from the end, as in Python, so -1 is the last item.
    """
    if count <= 0:
        raise ValueError("the list is empty, so there is nothing at any index")
    if index < 0:
        index += count
    if 0 <= index < count:
        return index
    if mode == "wrap":
        return index % count
    if mode == "clamp":
        return 0 if index < 0 else count - 1
    raise IndexError(
        f"index {index} is outside a list of {count} item(s); "
        "set mode to wrap or clamp to allow it"
    )


class SimpleListPicker:
    """Return the item at ``index`` from a list."""

    # Without this the executor calls us once per item and the index is moot.
    INPUT_IS_LIST = True

    RETURN_TYPES = (ANY, "INT", "INT")
    RETURN_NAMES = ("item", "resolved_index", "count")
    # Our outputs are single values even though our input was a list.
    OUTPUT_IS_LIST = (False, False, False)
    FUNCTION = "pick"
    CATEGORY = "utils"
    DESCRIPTION = "Pick one item out of a list by index."

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "items": (ANY, {"tooltip": "A list output, e.g. from Create List."}),
                "index": (
                    "INT",
                    {
                        "default": 0,
                        "min": -0xFFFFFFFFFFFFFFFF,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "step": 1,
                        # Set this to "increment" to walk the list one step per
                        # queued job, the way a seed advances.
                        "control_after_generate": True,
                        "tooltip": "Negative counts from the end, as in Python.",
                    },
                ),
                "mode": (
                    list(MODES),
                    {
                        "default": "wrap",
                        "tooltip": "Out of range: wrap around, clamp to the ends, "
                        "or raise an error.",
                    },
                ),
            }
        }

    def pick(self, items: Any, index: Any, mode: Any) -> tuple[Any, int, int]:
        if not isinstance(items, list):
            # A socket that was not a list output, or a single value: treat it
            # as a list of one rather than failing on something workable.
            items = [items]
        index = int(_single(index) or 0)
        mode = str(_single(mode) or "wrap")
        resolved = resolve_index(index, len(items), mode)
        return (items[resolved], resolved, len(items))


NODE_CLASS_MAPPINGS = {"SimpleListPicker": SimpleListPicker}
NODE_DISPLAY_NAME_MAPPINGS = {"SimpleListPicker": "Simple List Picker"}
