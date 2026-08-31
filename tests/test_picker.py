"""The picker, and the list semantics it exists to get right."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nodes import ANY, MODES, SimpleListPicker, resolve_index  # noqa: E402

PROMPTS = ["a cat", "a dog", "a bird"]


@pytest.fixture
def picker():
    return SimpleListPicker()


def test_it_declares_that_it_wants_the_whole_list():
    """Without INPUT_IS_LIST the executor calls the node once per item.

    That is what makes an otherwise-correct indexing node appear to ignore its
    index, so it is worth pinning rather than trusting.
    """
    assert SimpleListPicker.INPUT_IS_LIST is True
    assert SimpleListPicker.OUTPUT_IS_LIST == (False, False, False)


def test_it_returns_the_item_at_the_index(picker):
    item, resolved, count = picker.pick(PROMPTS, [1], ["wrap"])
    assert item == "a dog"
    assert (resolved, count) == (1, 3)


def test_scalar_widgets_arrive_wrapped_in_lists(picker):
    """INPUT_IS_LIST wraps *every* input, including the INT and the combo."""
    assert picker.pick(PROMPTS, [2], ["wrap"])[0] == "a bird"
    # Unwrapped values must work too, so the class stays usable from Python.
    assert picker.pick(PROMPTS, 2, "wrap")[0] == "a bird"


def test_a_negative_index_counts_from_the_end(picker):
    assert picker.pick(PROMPTS, [-1], ["wrap"])[0] == "a bird"
    assert picker.pick(PROMPTS, [-3], ["wrap"])[0] == "a cat"


def test_wrap_keeps_walking_past_the_end(picker):
    """The point of increment-per-queue: run 7 jobs over 3 prompts."""
    picked = [picker.pick(PROMPTS, [i], ["wrap"])[0] for i in range(7)]
    assert picked == ["a cat", "a dog", "a bird", "a cat", "a dog", "a bird", "a cat"]


def test_clamp_stops_at_the_ends(picker):
    assert picker.pick(PROMPTS, [99], ["clamp"])[0] == "a bird"
    assert picker.pick(PROMPTS, [-99], ["clamp"])[0] == "a cat"


def test_error_mode_says_what_went_wrong(picker):
    with pytest.raises(IndexError, match="outside a list of 3"):
        picker.pick(PROMPTS, [5], ["error"])


def test_an_empty_list_is_reported_clearly(picker):
    with pytest.raises(ValueError, match="empty"):
        picker.pick([], [0], ["wrap"])


def test_a_lone_value_is_treated_as_a_list_of_one(picker):
    """A socket that was not a list output should still work."""
    item, resolved, count = picker.pick("only", [0], ["wrap"])
    assert (item, resolved, count) == ("only", 0, 1)


def test_it_carries_any_type_not_just_strings(picker):
    objects = [{"a": 1}, [2], 3.5]
    assert picker.pick(objects, [1], ["wrap"])[0] == [2]
    assert picker.pick(objects, [2], ["wrap"])[0] == 3.5


def test_the_any_socket_accepts_every_type():
    """ComfyUI compares type strings to decide if a link is legal."""
    for other in ("STRING", "IMAGE", "LATENT", "INT", "MY_CUSTOM_TYPE"):
        assert not (ANY != other)
        assert ANY == other


def test_the_index_widget_can_step_per_queued_job():
    """control_after_generate is what makes "one item per run" work."""
    spec = SimpleListPicker.INPUT_TYPES()["required"]["index"][1]
    assert spec["control_after_generate"] is True
    assert spec["min"] < 0, "negative indices must be reachable from the widget"


def test_modes_offered_by_the_widget_are_the_modes_implemented():
    offered = SimpleListPicker.INPUT_TYPES()["required"]["mode"][0]
    assert tuple(offered) == MODES
    for mode in offered:
        resolve_index(0, 1, mode)


@pytest.mark.parametrize("count", [1, 2, 3, 10])
def test_wrap_never_leaves_the_list(count):
    for index in range(-3 * count, 3 * count):
        assert 0 <= resolve_index(index, count, "wrap") < count
