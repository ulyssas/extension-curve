"""
VNPathElement, pathGeometry
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import inkex

from .base import VNBaseElement
from .styles import VNColor, VNGradient, brushProfile, pathStrokeStyle


@dataclass
class VNPathElement(VNBaseElement):
    """Path Element properties."""

    mask: bool  # 0 or 1
    fillColor: Optional[VNColor]
    fillGradient: Optional[VNGradient]
    strokeStyle: Optional[pathStrokeStyle]
    brushProfile: Optional[brushProfile]
    # It's list because compoundPath has multiple pathGeometries
    pathGeometries: List[pathGeometry]
    shapeDescription: Optional[str]


class pathGeometry:
    """path format in Linearity Curve(nodes)."""

    def __init__(self, closed: bool, nodes: List[Dict]):
        self.corner_radius: List[float] = []
        self.path = self.parse_nodes(closed, nodes)

    def __repr__(self):
        return f"pathGeometry(path: {self.path}, corner_radius: {self.corner_radius})"

    def parse_nodes(self, closed: bool, nodes: List[Dict]) -> inkex.Path:
        """Converts single pathGeometry data to inkex path."""
        path = inkex.Path()
        prev = None
        outpt = None

        if closed and nodes:
            nodes.append(nodes[0])

        for node in nodes:
            # Path data is stored as  list of [inPoint, anchor, outPoint]
            # (plus some extra attributes for which we don't have enough data atm)
            anchor = inkex.Vector2d(node["anchorPoint"])

            if len(path) == 0:
                path.append(inkex.paths.Move(*anchor))
            else:
                inpt = inkex.Vector2d(node["inPoint"])
                anchor = inkex.Vector2d(node["anchorPoint"])

                # added * to add support for Inkscape 1.3
                if prev is not None and inpt is not None and outpt is not None:
                    if prev.is_close(outpt) and inpt.is_close(anchor):
                        path.append(inkex.paths.Line(*anchor))
                    else:
                        path.append(inkex.paths.Curve(*outpt, *inpt, *anchor))

            prev = anchor
            outpt = inkex.Vector2d(node["outPoint"])

            # add corner radius to the list if the node is sharp
            # nodeType(Curve Only): "disconnected", "asymmetric", "symmetric"
            node_type = node.get("nodeType")
            if node_type is not None:
                if isinstance(node_type.get("disconnected"), dict):
                    self.corner_radius.append(node["cornerRadius"])

        if path is not None and closed:
            path.append(inkex.paths.ZoneClose())

        return path
