"""
VNArtboard, Frame, VNLayer
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .base import VNBaseElement
from .styles import VNColor, VNGradient


@dataclass
class VNArtboard:
    """Represents Linearity Curve Artboard."""

    title: str
    frame: Frame
    layers: List[VNLayer]
    guides: Optional[List[VNBaseElement]]
    fillColor: Optional[VNColor]
    fillGradient: Optional[VNGradient]


@dataclass
class Frame:
    """Artboard frame."""

    width: float
    height: float
    x: float
    y: float


@dataclass
class VNLayer:
    """Represents Linearity Curve Layer."""

    name: str
    opacity: float
    isVisible: bool
    isLocked: bool
    isExpanded: bool
    elements: List[VNBaseElement]
