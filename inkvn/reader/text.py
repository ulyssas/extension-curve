"""
VI text tools

Decodes Linearity Curve styledTexts and turn them into simpler format.
"""

import copy
from typing import Any, Dict, List

from inkex.utils import debug


def decode_new_text(styled_text: Dict) -> List[Dict]:
    """Decodes upperBound system used by Newer text format, preserving nested structure."""

    def _collect_upper_bounds(attrib: Dict, upper_bounds: List[int]):
        """collect all upperBounds inside, without duplication"""
        values = attrib.get("values")
        if values:
            for val in values:
                ub = val["upperBound"]
                if ub not in upper_bounds:
                    upper_bounds.append(ub)
        else:
            for v in attrib.values():
                if isinstance(v, dict):
                    # recursively collect upperBound
                    _collect_upper_bounds(v, upper_bounds)

    def _insert_value_by_path(d: Dict, path: List[str], value: Any):
        """Utility to insert value into nested dictionary via path list."""
        for key in path[:-1]:
            # deeper in the dictionary
            d = d.setdefault(key, {})
        d[path[-1]] = value

    def _add_styles(
        attrib: Dict, path: List[str], upper_bounds: List[int], styles: List[Dict]
    ):
        """add style and its effective range to list of `styles`"""
        values = attrib.get("values")
        if values:
            for val in values:
                ub = val["upperBound"]
                index = upper_bounds.index(ub)
                _insert_value_by_path(styles[index], path, val["value"])

                if index == 0:
                    styles[index]["length"] = ub
                else:
                    styles[index]["length"] = ub - upper_bounds[index - 1]
        else:
            for key, child in attrib.items():
                if isinstance(child, dict):
                    _add_styles(child, path + [key], upper_bounds, styles)

    def _propagate_values(styles: List[Dict]):
        """apply any missing styles with its previous style."""
        if not styles:
            return

        propagated_attrs = copy.deepcopy(styles[-1])

        for style in reversed(styles):
            # top-level
            for key, value in propagated_attrs.items():
                if key not in style:
                    style[key] = copy.deepcopy(value)

            key = "strokeStyle"
            if (
                key in style
                and isinstance(style.get(key), dict)
                and key in propagated_attrs
                and isinstance(propagated_attrs.get(key), dict)
            ):
                # add missing values (color, width)
                for sub_key, sub_value in propagated_attrs[key].items():
                    if sub_key not in style[key]:
                        style[key][sub_key] = sub_value

            # update propagated_attrs with current
            for key, value in style.items():
                if key == "strokeStyle" and isinstance(value, dict):
                    if not isinstance(propagated_attrs.get(key), dict):
                        propagated_attrs[key] = {}
                    propagated_attrs[key].update(value)
                else:
                    propagated_attrs[key] = value

    upper_bounds: List[int] = []
    for key, val in styled_text.items():
        if isinstance(val, dict):
            _collect_upper_bounds(val, upper_bounds)
    upper_bounds.sort()

    styles: List[Dict] = [{} for _ in upper_bounds]

    for key, val in styled_text.items():
        if isinstance(val, dict):
            _add_styles(val, [key], upper_bounds, styles)

    _propagate_values(styles)

    return styles


def decode_old_text(unserialized: Dict) -> List[Dict]:
    """Decodes legacy text unpacked by NSKeyUnarchiver."""
    # string has already been processed
    string = unserialized["NSString"]
    lengths = unserialized.get("NSAttributeInfo")
    styles = unserialized["NSAttributes"]

    formatted_data: List[Dict] = []

    # if text only contains one style
    if isinstance(styles, dict):
        lengths = [{"length": len(string), "attribute_id": 0}]
        styles = [styles]

    # empty
    if lengths is None:
        return formatted_data

    for length_info in lengths:
        length = length_info["length"]
        attribute_id = length_info["attribute_id"]

        # checking if NSAttributeInfo has successfully parsed
        if not styles or attribute_id < 0 or attribute_id >= len(styles):
            debug(
                f"Error: attribute_id {attribute_id} is out of range. styles length: {len(styles)}"
            )

        attribute = styles[attribute_id]

        # strokeStyle without basicStrokeStyle
        stroke_style = None
        ns_stroke_color = attribute.get("NSStrokeColor")
        if ns_stroke_color and isinstance(ns_stroke_color, dict):
            stroke_style = {
                "color": {
                    "rgba": {
                        "red": ns_stroke_color.get("UIRed", 0.0),
                        "green": ns_stroke_color.get("UIGreen", 0.0),
                        "blue": ns_stroke_color.get("UIBlue", 0.0),
                        "alpha": ns_stroke_color.get("UIAlpha", 1.0),
                    },
                },
                "width": max(0, attribute.get("NSStrokeWidth", 1.0)),
            }
            if stroke_style["width"] <= 0:
                stroke_style = None

        # color
        color_data = None
        ns_color = attribute.get("NSColor")
        if ns_color and isinstance(ns_color, dict):
            color_data = {
                "rgba": {
                    "red": ns_color.get("UIRed", 0.0),
                    "green": ns_color.get("UIGreen", 0.0),
                    "blue": ns_color.get("UIBlue", 0.0),
                    "alpha": ns_color.get("UIAlpha", 1.0),
                }
            }

        # paragraph
        paragraph_style = attribute.get("NSParagraphStyle")

        # font
        ns_font = attribute.get("NSFont")

        # strikethrough, underline
        ns_strike = bool(attribute.get("NSStrikethrough", 0))
        ns_underline = bool(attribute.get("NSUnderline", 0))

        alignment = paragraph_style.get("NSAlignment", 0)
        # swap 1 & 2 (right & center)
        if alignment in (1, 2):
            alignment = 3 - alignment

        # TODO Include lineHeight and kerning
        formatted_data.append(
            {
                "alignment": alignment,
                "length": length,
                "strokeStyle": stroke_style,
                "fillColor": color_data,
                "fontName": ns_font["NSName"],
                "fontSize": ns_font["NSSize"],
                "kerning": 0,
                "lineHeight": None,
                "strikethrough": ns_strike,
                "underline": ns_underline,
            }
        )

    return formatted_data
