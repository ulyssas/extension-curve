"""
VNGuideElement
"""

from dataclasses import dataclass

from .base import VNBaseElement


@dataclass
class VNGuideElement(VNBaseElement):
    """Guide element."""

    offset: float
    orientation: int
    """0 means vertical and 1 means horizontal."""
