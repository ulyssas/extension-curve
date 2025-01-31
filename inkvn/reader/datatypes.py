"""
Classes to be used in read.py & convert.py

Intermediate data format in inkvn
"""

from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import inkex


@dataclass
class BaseElement:
    """Common Element properties."""
    name: str
    blur: float
    opacity: float
    blendMode: int
    isHidden: bool
    isLocked: bool
    localTransform: localTransform

    @staticmethod
    def blend_mode_to_svg(blendmode: int) -> str:
        """Returns value for mix-blend-mode attribute."""
        blend_mode_map = {
            0: "normal",
            1: "multiply",
            2: "screen",
            3: "overlay",
            4: "darken",
            5: "lighten",
            10: "difference",
            11: "exclusion",
            12: "hue",
            13: "saturation",
            14: "color",
            15: "luminosity",
        }
        return blend_mode_map.get(blendmode, "normal")


@dataclass
class ImageElement(BaseElement):
    imageData: str


# TODO WHAT WILL HAPPEN>>>????
@dataclass
class PathElement(BaseElement):
    fill: Optional[Color]
    fillId: Optional[int]
    strokeStyle: Optional[pathStrokeStyle]
    pathGeometry: Dict


# No text for now
# @dataclass
# class TextElement(BaseElement):
#     styledText
#     textProperty


@dataclass
class GroupElement(BaseElement):
    groupElements: List[BaseElement]


@dataclass
class Layer:
    name: str
    opacity: float
    isVisible: bool
    isLocked: bool
    isExpanded: bool
    elements: List[BaseElement]


@dataclass
class Artboard:
    title: str
    frame: Frame
    layers: List[Layer]


@dataclass
class Frame:
    """Artboard frame"""
    width: float
    height: float
    x: float
    y: float


@dataclass
class localTransform:
    rotation: float = 0.0
    scale: List[float] = field(default_factory=lambda: [1.0, 1.0])
    shear: float = 0.0
    translation: List[float] = field(default_factory=lambda: [0.0, 0.0])

    def create_transform(self, keep_proportion=False) -> inkex.transforms.Transform:
        """
        Creates a transform string for the `g` element in inkex.transforms.Transform.
        """

        # Extract values
        rotation_deg = math.degrees(self.rotation)
        sx, sy = self.scale
        # Shear is given in radians
        shear_deg = math.degrees(math.atan(self.shear))
        tx, ty = self.translation

        # Create transform components
        # The order matters
        tr = inkex.transforms.Transform()
        if tx != 0 or ty != 0:
            # Translate by (tx, ty)
            tr.add_translate(tx, ty)

        if self.rotation != 0:
            # Rotate around origin (adjust if a specific pivot is needed)
            tr.add_rotate(rotation_deg)

        if sx != 1 or sy != 1:
            # Scale by (sx, sy)
            if keep_proportion == True:
                tr.add_scale(sx)
            else:
                tr.add_scale(sx, sy)

        if self.shear != 0:
            # Skew in the X direction
            tr.add_skewx(shear_deg)

        return tr


@dataclass
class pathGeometry:
    """path format in Linearity Curve."""
    closed: bool
    nodes: List[Dict]


class Color:
    """
    Represents a color with hex and alpha values.

    for styledTexts-fillColor-value,
    pathStrokeStyles-color and fills-color.
    """

    def __init__(self, color_dict: Dict):
        """
        Initializes the Color object from a dictionary containing color data.
        Handles both HSBA and RGBA formats.
        """
        self.hex: str = "#000000"
        self.alpha: float = 1.0

        color_data = self._extract_color_data(color_dict)
        if color_data is None:
            raise ValueError("Invalid color format")

        self.hex, self.alpha = color_data

    def _extract_color_data(self, color_dict: Dict) -> Optional[Tuple[str, float]]:
        """
        Extracts hex and alpha values from the given dictionary.
        Returns None if no valid color data is found.
        """
        rgba = color_dict.get("rgba")
        hsba = color_dict.get("hsba")

        if rgba:
            r, g, b, a = self._rgba_to_tuple(rgba)
        elif hsba:
            r, g, b, a = self._hsba_to_rgba_tuple(hsba)
        else:
            return None

        hex_color = self._rgba_to_hex((r, g, b, a))
        return hex_color, a

    def _hsba_to_rgba_tuple(self, hsba: Dict) -> Tuple[float, float, float, float]:
        """Converts an HSBA color to RGBA format."""
        hue = hsba.get("hue", 0)
        saturation = hsba.get("saturation", 0)
        brightness = hsba.get("brightness", 0)
        alpha = hsba.get("alpha", 1)

        r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
        return r, g, b, alpha

    def _rgba_to_tuple(self, rgba: Dict) -> Tuple[float, float, float, float]:
        """Converts an RGBA color to tuple format."""
        red = rgba.get("red", 0)
        green = rgba.get("green", 0)
        blue = rgba.get("blue", 0)
        alpha = rgba.get("alpha", 1)

        return red, green, blue, alpha

    def _rgba_to_hex(self, rgba: Tuple[float, float, float, float]) -> str:
        """Converts RGBA tuple into str hex (#RRGGBB)."""
        r, g, b, _ = rgba
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)

        return f"#{r:02X}{g:02X}{b:02X}"


@dataclass
class pathStrokeStyle:
    basicStrokeStyle: basicStrokeStyle
    color: Color
    width: float


class basicStrokeStyle:
    def __init__(self, cap: int, dashPattern: Optional[List[float]], join: int, position: int):
        self.cap: str = self.cap_to_svg(cap)
        self.dashPattern: List[float] = dashPattern if dashPattern is not None else [0, 0, 0, 0]
        self.join: str = self.join_to_svg(join)
        self.position: int = position

    @staticmethod
    def cap_to_svg(cap):
        """Returns value for stroke-linecap attribute."""
        cap_map = {
            0: "butt",
            1: "round",
            2: "square"
        }
        return cap_map.get(cap, "butt")

    @staticmethod
    def join_to_svg(join: int) -> str:
        """Returns value for stroke-linejoin attribute."""
        join_map = {
            0: "miter",
            1: "round",
            2: "bevel",
        }
        return join_map.get(join, "miter")
