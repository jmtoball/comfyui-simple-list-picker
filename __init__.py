"""Simple List Picker -- a ComfyUI custom node.

One node: give it a list and an index, get back the item. Set the index widget's
control_after_generate to ``increment`` and each queued job takes the next item.
"""

from __future__ import annotations

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
