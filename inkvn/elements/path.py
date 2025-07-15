"""
VNPathElement, pathGeometry, shapeParameter
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import inkex

from inkvn.const import CurveShape

from .base import VNBaseElement
from .styles import VNColor, VNGradient, brushProfile, pathStrokeStyle


@dataclass
class VNPathElement(VNBaseElement):
    """Path Element properties."""

    mask: bool
    fillColor: Optional[VNColor]
    fillGradient: Optional[VNGradient]
    strokeStyle: Optional[pathStrokeStyle]
    brushProfile: Optional[brushProfile]
    # It's list because compoundPath has multiple pathGeometries
    pathGeometries: List[pathGeometry]
    shapeDescription: Optional[str]
    shapeParameter: Optional[shapeParameter]

    def convert_shape(
        self, path: inkex.PathElement, has_transform_applied: bool
    ) -> Optional[inkex.ShapeElement]:
        """Return inkex.ShapeElement (only Rectangle for now)."""

        # TODO スケールだけ適用できないか?

        # avoid creating shape for open path
        if not all(p.closed for p in self.pathGeometries):
            return None

        # don't create shapes if both are missing
        if not self.shapeDescription and not self.shapeParameter:
            return None

        # Rectangle
        if self.shapeDescription == CurveShape.RECT:
            return self._convert_rect(path, has_transform_applied)

        return None

    def _convert_rect(
        self, path: inkex.PathElement, has_transform_applied: bool
    ) -> Optional[inkex.Rectangle]:
        # rectangle cannot have smooth nodes
        # TODO this could cause rounded rect to not work?
        if not all(p.is_sharp for p in self.pathGeometries):
            return None

        original_tr = path.transform
        try:
            # undo transform to get original path
            if has_transform_applied and self.localTransform:
                path.transform = -self.localTransform.convert_transform()

            bbox = path.bounding_box()
            if not bbox:
                return None
            rect = inkex.Rectangle.new(bbox.left, bbox.top, bbox.width, bbox.height)

            # apply transform to Vectornator shape
            if has_transform_applied and self.localTransform is not None:
                rect.transform = self.localTransform.convert_transform()

            self._set_rect_corner(rect)

            return rect

        finally:
            path.transform = original_tr

    def _set_rect_corner(self, rect: inkex.Rectangle):
        if not self.localTransform:
            return

        rx = None
        if self.shapeParameter:
            rx = self.shapeParameter.corner_radius()
        else:
            if self.pathGeometries[0].corner_radius:
                rx = self.pathGeometries[0].corner_radius[0]

        if rx is None or rx <= 0:
            return

        sx, sy = self.localTransform.scale

        if sx != 0:
            rect.set("rx", rx / abs(sx))

        if not math.isclose(abs(sx), abs(sy)):
            if sy != 0:
                rect.set("ry", rx / abs(sy))


class pathGeometry:
    """path format in Linearity Curve(nodes)."""

    def __init__(self, closed: bool, nodes: List[Dict]):
        self.corner_radius: List[float] = []
        self.path = self.parse_nodes(closed, nodes)
        self.closed = closed
        self.is_sharp: bool  # used to determine path has smooth corner or not

    def __repr__(self):
        return f"pathGeometry(path: {self.path}, corner_radius: {self.corner_radius})"

    def parse_nodes(self, closed: bool, nodes: List[Dict]) -> inkex.Path:
        """Converts single pathGeometry data to inkex path."""
        path = inkex.Path()
        prev = None
        outpt = None
        self.is_sharp = True

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
                else:
                    self.is_sharp = False

        if path is not None and closed:
            path.append(inkex.paths.ZoneClose())

        return path


@dataclass
class shapeParameter:
    """Optional shape params in Linearity Curve."""

    additionalValue: Dict
    initialPoint: Tuple[float, float]  # top-left with transform applied
    endPoint: Tuple[float, float]  # bottom-right with transform applied

    def corner_radius(self) -> Optional[float]:
        """Return cornerRadius in `additionalValue`. Only rectangle contains this value."""

        rect = self.additionalValue.get("rectangle")
        if rect is not None:
            return rect["cornerRadius"]
        return None
