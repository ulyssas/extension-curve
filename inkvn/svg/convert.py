"""
inkvn Converter

Convert the intermediate data to Inkscape read by read.py
"""

from typing import List, Optional

import inkex
from inkex.base import SvgOutputMixin
import lxml.etree

from inkvn.reader.datatypes import (
    Artboard, BaseElement, Color, GroupElement, Gradient,
    ImageElement, PathElement, pathStrokeStyle
)
from inkvn.reader.read import CurveReader


class CurveConverter():
    def __init__(self) -> None:
        self.reader: CurveReader
        self.target_version: int
        self.has_transform_applied: bool
        self.doc: lxml.etree._ElementTree
        self.document: inkex.SvgDocumentElement
        self.offset_x: float
        self.offset_y: float

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

        first_artboard = reader.artboards[0]

        self.doc = SvgOutputMixin.get_template(
            width=first_artboard.frame.width,
            height=first_artboard.frame.height,
        )
        self.document = self.doc.getroot()

        # Adding comments
        comment = lxml.etree.Comment(" Converted by extension-curve ")
        self.document.addprevious(comment)

        # first artboard becomes the front page
        self.offset_x = first_artboard.frame.x
        self.offset_y = first_artboard.frame.y

        for target_artboard in reader.artboards:
            page = inkex.Page.new(
                width=target_artboard.frame.width,
                height=target_artboard.frame.height,
                x=target_artboard.frame.x - self.offset_x,
                y=target_artboard.frame.y - self.offset_y,
            )
            self.document.namedview.add(page)
            page.set("inkscape:label", target_artboard.title)

            self.load_page(
                self.document.add(inkex.Layer.new(label=target_artboard.title)), target_artboard
            )
            self.doc.getroot()

    def load_page(self, root_layer: inkex.Layer, artboard: Artboard) -> None:
        """Convert inkvn artboard to inkex page."""

        # artboards have translations
        tr = inkex.transforms.Transform()
        tr.add_translate(
            artboard.frame.x - self.offset_x,
            artboard.frame.y - self.offset_y
        )
        root_layer.transform = tr

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
        group.style["opacity"] = group_element.opacity
        group.style["mix-blend-mode"] = group_element.blend_to_str()
        group.style["display"] = "none" if group_element.isHidden else "inline"
        if group_element.isLocked:
            group.set("sodipodi:insensitive", "true")
        if not self.has_transform_applied and group_element.localTransform:
            group.transform = group_element.localTransform.create_transform()

        # blur
        if group_element.blur > 0:
            self.set_blur(group, group_element.convert_blur())

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
        image.style["opacity"] = image_element.opacity
        image.style["mix-blend-mode"] = image_element.blend_to_str()
        image.style["display"] = "none" if image_element.isHidden else "inline"
        if image_element.isLocked:
            image.set("sodipodi:insensitive", "true")
        if not self.has_transform_applied and image_element.localTransform:
            image.transform = image_element.localTransform.create_transform()
        elif image_element.transform:
            image.transform = image_element.transform

        # blur
        if image_element.blur > 0:
            self.set_blur(image, image_element.convert_blur())

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
                path.path += path_geometry.path

        if not self.has_transform_applied and path_element.localTransform:
            path.transform = path_element.localTransform.create_transform()

            # Apply Transform
            path = inkex.PathElement.new(path.get_path().transform(path.transform))

        # PathEffect(corner), does not work for other paths in compoundPath
        if path_element.pathGeometries[0].corner_radius:
            corner_radius = path_element.pathGeometries[0].corner_radius
            if any(corner_radius):  # only if there are values other than 0
                self.set_corner(path, corner_radius)

        # BaseElement
        path.label = path_element.name
        path.style["opacity"] = path_element.opacity
        path.style["mix-blend-mode"] = path_element.blend_to_str()
        path.style["display"] = "none" if path_element.isHidden else "inline"
        if path_element.isLocked:
            path.set("sodipodi:insensitive", "true")

        # blur
        if path_element.blur > 0:
            self.set_blur(path, path_element.convert_blur())

        # Stroke Style
        if path_element.strokeStyle:
            self.set_stroke_styles(path, path_element.strokeStyle)
        else:
            path.style["stroke"] = "none"

        # Fill Style
        if path_element.fillColor:
            self.set_fill_color_styles(path, path_element.fillColor)
        elif path_element.fillGradient:

            # Add gradientTransform
            # matrix transform is based on Vectornator 4.13.2, format 13
            # and Linearity Curve 5.1.1, format 21
            if path_element.fillGradient.transform:
                path_element.fillGradient.gradient.set("gradientTransform", path_element.fillGradient.transform)

            elif path_element.localTransform and not self.has_transform_applied:
                gradient_transform = path_element.localTransform.create_transform()
                path_element.fillGradient.gradient.set("gradientTransform", gradient_transform)

            self.set_fill_grad_styles(path, path_element.fillGradient)
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
        path.style["mix-blend-mode"] = base_element.blend_to_str()
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

    def set_fill_color_styles(self, elem: inkex.BaseElement, fill: Color) -> None:
        """Apply fillColor to inkex.BaseElement."""
        elem.style["fill"] = fill.hex
        elem.style["fill-opacity"] = fill.alpha
        elem.style["fill-rule"] = "nonzero"

    def set_fill_grad_styles(self, elem: inkex.BaseElement, fill: Gradient) -> None:
        """Apply fillGradient to inkex.BaseElement."""
        self.document.defs.add(fill.gradient)
        elem.style["fill"] = f"url(#{fill.gradient.get_id()})"
        # elem.style["fill-opacity"] = fill.alpha # ??
        elem.style["fill-rule"] = "nonzero"

    def set_blur(self, elem: inkex.BaseElement, blur: inkex.Filter.GaussianBlur) -> None:
        """Apply blur to inkex.BaseElement."""
        filter: inkex.Filter = inkex.Filter()
        filter.set("color-interpolation-filters", "sRGB")
        filter.add(blur)
        self.document.defs.add(filter)

        # Only one filter will be there
        elem.style["filter"] = f"url(#{filter.get_id()})"

    def set_corner(self, elem: inkex.PathElement, corner_radius: List[float]) -> None:
        """Apply rounded corner to inkex.PathElement."""
        params = " @ ".join(
            f"F,0,0,1,0,{r},0,1"
            for r in corner_radius
        )

        # TODO more cornerRadius work
        #  flexible="false" is how Linearity Curve behaved,
        #  but this is not optimal
        path_effect = inkex.PathEffect.new(
            effect="fillet_chamfer",
            lpeversion="1",
            method="auto",
            flexible="false",
            is_visible="true",
            satellites_param=params,  # Inkscape 1.2
            nodesatellites_param=params,  # Inkscape 1.3
        )

        self.document.defs.add(path_effect)
        elem.set("inkscape:original-d", str(elem.path))
        elem.set(
            "inkscape:path-effect", f"{path_effect.get_id(1)}"
        )
        elem.attrib.pop("d", None)  # delete "d", Inkscape auto-generates LPE path

