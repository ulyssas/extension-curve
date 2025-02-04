"""
inkvn Converter

Convert the intermediate data read by read.py
"""

from dataclasses import asdict

from typing import Any, Dict, Optional, Tuple

import inkex
from inkex.base import SvgOutputMixin
import lxml.etree

from inkvn.reader.datatypes import (
    Artboard, BaseElement, Color, Frame, GroupElement,
    ImageElement, Layer, PathElement, basicStrokeStyle,
    localTransform, pathGeometry, pathStrokeStyle
)
from inkvn.reader.read import CurveReader


class CurveConverter():
    def __init__(self) -> None:
        self.reader: CurveReader
        self.target_version: int
        self.has_transform_applied: bool
        self.doc: lxml.etree._ElementTree
        self.document: inkex.SvgDocumentElement

    def convert(self, reader: CurveReader) -> None:
        self.reader = reader

        """
        file version check

        New curve holds path data without transforms
        However, old curve has transforms already applied.
        I don't know exactly when the behavior has changed, so it's set to 44
        """
        if reader.file_version < 44:
            self.has_transform_applied = True
        else:
            self.has_transform_applied = False

        target_artboard = reader.artboards[0]

        # TODO: @Convert fix for multiple artboards
        self.doc = SvgOutputMixin.get_template(
            width=target_artboard.frame.width,
            height=target_artboard.frame.height,
        )
        self.document = self.doc.getroot()

        # Adding comments
        comment = lxml.etree.Comment("Converted by extension-curve")
        self.document.addprevious(comment)

        page = inkex.Page.new(**asdict(target_artboard.frame))  # includes x, y
        self.document.namedview.add(page)
        page.set("inkscape:label", target_artboard.title)

        self.load_page(
            self.document.add(inkex.Layer.new(label=target_artboard.title)), target_artboard
        )
        self.doc.getroot()

    def load_page(self, root_layer: inkex.Layer, artboard: Artboard) -> None:
        """Convert inkvn artboard to inkex page."""
        # layers in the artboard
        for layer in artboard.layers:
            parent = root_layer.add(inkex.Layer.new(layer.name))
            parent.set("opacity", layer.opacity)
            parent.style["display"] = (
                "inline" if layer.isVisible else "none"
            )
            if layer.isLocked:
                parent.set("sodipodi:insensitive", "true")
            # ? isExpanded

            # elements in the layer
            for element in layer.elements:
                elm = self.load_element(element)
                if elm is not None:
                    parent.add(elm)

    def load_element(self, element: BaseElement) -> Optional[inkex.BaseElement]:
        """Converts an element to an SVG element."""
        if isinstance(element, GroupElement):
            return self.convert_group(element)
        elif isinstance(element, ImageElement):
            return self.convert_image(element)
        elif isinstance(element, PathElement):
            return self.convert_path(element)
        # TODO TEXT
        elif isinstance(element, BaseElement):
            return self.convert_base(element)  # will be empty path element
        else:
            inkex.utils.debug(f"Unsupported element type: {type(element)}")
            return None

    def convert_group(self, group_element: GroupElement) -> inkex.Group:
        """Converts a GroupElement to an SVG group (inkex.Group)."""
        group = inkex.Group()

        # BaseElement
        group.label = group_element.name
        # TODO blur
        group.style["opacity"] = group_element.opacity
        group.style["mix-blend-mode"] = group_element.blend_to_str(group_element.blendMode)
        group.style["display"] = "none" if group_element.isHidden else "inline"
        if group_element.isLocked:
            group.set("sodipodi:insensitive", "true")
        if not self.has_transform_applied and group_element.localTransform:
            group.transform = group_element.localTransform.create_transform()

        for child in group_element.groupElements:
            svg_element = self.load_element(child)
            if svg_element is not None:
                group.add(svg_element)

        return group

    def convert_image(self, image_element: ImageElement) -> inkex.Image:
        """Converts an ImageElement to an SVG image (inkex.Image)."""
        image = inkex.Image()

        # BaseElement
        image.label = image_element.name
        # TODO blur
        image.style["opacity"] = image_element.opacity
        image.style["mix-blend-mode"] = image_element.blend_to_str(image_element.blendMode)
        image.style["display"] = "none" if image_element.isHidden else "inline"
        if image_element.isLocked:
            image.set("sodipodi:insensitive", "true")
        if not self.has_transform_applied and image_element.localTransform:
            image.transform = image_element.localTransform.create_transform()
        elif image_element.transform:
            image.transform = image_element.transform

        # Image
        img_format = image_element.image_format()
        width, height = image_element.image_dimension()

        image.set("preserveAspectRatio", "none")
        image.set(
            inkex.addNS("href", "xlink"),
            f"data:image/{img_format.lower()};base64,{image_element.imageData}",
        )
        image.set("width", width)
        image.set("height", height)

        return image

    def convert_path(self, path_element: PathElement) -> inkex.PathElement:
        """Converts a PathElement to an SVG path (inkex.PathElement)."""
        path = inkex.PathElement()

        # pathGeometry
        if path_element.pathGeometries:
            for path_geometry in path_element.pathGeometries:
                path.path += path_geometry.parse_nodes()

        if not self.has_transform_applied and path_element.localTransform:
            path.transform = path_element.localTransform.create_transform()

            # Apply Transform
            path = inkex.PathElement.new(path.get_path().transform(path.transform))

        # BaseElement
        path.label = path_element.name
        # TODO blur
        path.style["opacity"] = path_element.opacity
        path.style["mix-blend-mode"] = path_element.blend_to_str(path_element.blendMode)
        path.style["display"] = "none" if path_element.isHidden else "inline"
        if path_element.isLocked:
            path.set("sodipodi:insensitive", "true")

        # Stroke Style
        if path_element.strokeStyle:
            self.set_stroke_styles(path, path_element.strokeStyle)
        else:
            path.style["stroke"] = "none"

        # Fill Style
        if path_element.fill:
            self.set_fill_styles(path, path_element.fill)
        else:
            path.style["fill"] = "none"

        return path

    def convert_base(self, base_element: BaseElement) -> inkex.PathElement:
        """Converts a BaseElement to an empty SVG path (inkex.PathElement)."""
        inkex.utils.debug(f'{base_element.name}: This element will be imported as empty path.')

        path = inkex.PathElement()

        # BaseElement
        path.label = base_element.name
        path.style["opacity"] = base_element.opacity
        path.style["mix-blend-mode"] = base_element.blend_to_str(base_element.blendMode)
        path.style["display"] = "none" if base_element.isHidden else "inline"
        if base_element.isLocked:
            path.set("sodipodi:insensitive", "true")

        # Style
        path.style["stroke"] = "none"
        path.style["fill"] = "none"

        return path

    def set_stroke_styles(self, elem: inkex.BaseElement, stroke: pathStrokeStyle) -> None:
        """Apply pathStrokeStyle to inkex.BaseElement."""
        elem.style["stroke"] = stroke.color.hex
        elem.style["stroke-opacity"] = stroke.color.alpha
        elem.style["stroke-linecap"] = stroke.basicStrokeStyle.cap
        elem.style["stroke-linejoin"] = stroke.basicStrokeStyle.join
        elem.style["stroke-dasharray"] = stroke.basicStrokeStyle.dashPattern
        elem.style["stroke-width"] = stroke.width

    def set_fill_styles(self, elem: inkex.BaseElement, fill: Color) -> None:
        """Apply fill to inkex.BaseElement."""
        # TODO Gradient
        elem.style["fill"] = fill.hex
        elem.style["fill-opacity"] = fill.alpha
        elem.style["fill-rule"] = "nonzero"

