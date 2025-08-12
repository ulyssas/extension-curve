"""
VNBaseElement, VNTransform
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

import inkex


@dataclass
class VNBaseElement:
    """Common Element properties."""

    name: str
    blur: float
    opacity: float
    blendMode: int
    isHidden: bool
    isLocked: bool
    localTransform: Optional[VNTransform]

    def convert_blend(self) -> str:
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
        return blend_mode_map.get(self.blendMode, "normal")

    def convert_blur(self) -> inkex.Filter.GaussianBlur:
        """Returns inkex GaussianBlur."""
        """
        FIXME Blur does not work like it should.
        divided by 3 because I don't know
        """
        return inkex.Filter.GaussianBlur.new(
            stdDeviation=self.blur / 3.0, result="blur"
        )


@dataclass
class VNTransform:
    """Linearity Curve transform."""

    rotation: float = 0.0
    scale: List[float] = field(default_factory=lambda: [1.0, 1.0])
    shear: float = 0.0
    translation: List[float] = field(default_factory=lambda: [0.0, 0.0])

    def convert_transform(
        self, keep_proportion=False, with_scale=True
    ) -> inkex.transforms.Transform:
        """
        Creates a transform string in inkex.transforms.Transform.

        keep_proportion applies scaling in x axis to y axis as well.
        with_scale determines whether to include scale or not.
        """

        rotation_deg = math.degrees(self.rotation)
        sx, sy = self.scale
        # Shear is given in radians
        shear_deg = math.degrees(math.atan(self.shear))
        tx, ty = self.translation

        tr = inkex.transforms.Transform()
        if tx != 0 or ty != 0:
            tr.add_translate(tx, ty)

        if self.rotation != 0:
            tr.add_rotate(rotation_deg)

        if with_scale and (sx != 1 or sy != 1):
            if keep_proportion:
                tr.add_scale(sx)
            else:
                tr.add_scale(sx, sy)

        if self.shear != 0:
            tr.add_skewx(shear_deg)

        return tr

    def convert_scale(self, keep_proportion=False) -> inkex.transforms.Transform:
        """
        Creates a scale transform in inkex.transforms.Transform.

        keep_proportion applies scaling in x axis to y axis as well.
        """
        tr = inkex.transforms.Transform()
        sx, sy = self.scale

        if sx != 1 or sy != 1:
            if keep_proportion:
                tr.add_scale(sx)
            else:
                tr.add_scale(sx, sy)

        return tr
