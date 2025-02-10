"""
VNTextElement, styledText, textProperty
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .base import VNBaseElement


@dataclass
class VNTextElement(VNBaseElement):
    styledText: Optional[styledText]
    textProperty: Optional[textProperty]


@dataclass
class styledText:
    # List means different styles for each characters(upperBound)
    alignment: List[Dict]
    fillColor: List[Dict]
    fontName: List[Dict]
    fontSize: List[Dict]
    kerning: List[Dict]
    lineHeight: List[Dict]
    strikethrough: List[Dict]
    string: str
    underline: List[Dict]


@dataclass
class textProperty:
    # "fixedSize":{"height": float,"width": float}
    # autos don't contain values
    textFrameLimits: Dict  # autoWidth, autoHeight, fixedSize
    textFramePivot: Tuple[float, float]
