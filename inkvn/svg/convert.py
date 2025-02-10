"""
inkvn Converter

Convert the intermediate data to Inkscape read by read.py
"""

from typing import List, Optional

import inkex
from inkex.base import SvgOutputMixin
import lxml.etree

from ..reader.read import CurveReader

from ..elements.artboard import VNArtboard
from ..elements.base import VNBaseElement
from ..elements.guide import VNGuideElement
from ..elements.group import VNGroupElement
from ..elements.image import VNImageElement
from ..elements.path import VNPathElement
from ..elements.text import VNTextElement
from ..elements.styles import VNColor, VNGradient, pathStrokeStyle


class CurveConverter():
    """
    inkvn CurveConverter

    Convert the intermediate data to Inkscape.
    """
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
        I don't know exactly when the behavior has changed, so it's set to 30 as placeholder

        Curve 5.12.0, format 40 confirmed(works the same as 44)
        """
        if reader.file_version < 30:
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

    def load_page(self, root_layer: inkex.Layer, artboard: VNArtboard) -> None:
        """Convert  VNArtboard to inkex page."""

        # artboards have translations
        tr = inkex.transforms.Transform()
        tr_vector = inkex.Vector2d(
            artboard.frame.x - self.offset_x,
            artboard.frame.y - self.offset_y
        )
        tr.add_translate(tr_vector)
        root_layer.transform = tr

        # Artboard color/gradient
        rect = inkex.Rectangle.new(
            0, 0, artboard.frame.width, artboard.frame.height
        )
        rect.label = "background"

        # Fill Style
        if artboard.fillColor is not None:
            self.set_fill_color_styles(rect, artboard.fillColor)
            root_layer.add(rect)
        elif artboard.fillGradient is not None:
            if artboard.fillGradient.transform is not None:
                artboard.fillGradient.gradient.set("gradientTransform", artboard.fillGradient.transform)
            self.set_fill_grad_styles(rect, artboard.fillGradient)
            root_layer.add(rect)
        # if fill is none, rect will be dismissed

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

        # Guide
        for guide in artboard.guides:
            if guide is not None:
                self.add_guide(guide, tr_vector)

    def load_element(self, element: VNBaseElement) -> Optional[inkex.BaseElement]:
        """Converts an element to an SVG element."""
        if isinstance(element, VNGroupElement):
            return self.convert_group(element)

        elif isinstance(element, VNImageElement):
            return self.convert_image(element)

        elif isinstance(element, VNPathElement):
            return self.convert_path(element)

        elif isinstance(element, VNTextElement):
            # TODO TEXT
            inkex.utils.debug(f'{element.name}: Text has been successfully parsed, but text import is not supported yet.')
            return self.convert_base(element)

        elif isinstance(element, VNBaseElement):
            return self.convert_base(element)  # will be empty path element

        else:
            inkex.utils.debug(f"Unsupported element type: {type(element)}")
            return None

    def convert_group(self, group_element: VNGroupElement) -> inkex.Group:
        """Converts a VNGroupElement to an SVG group (inkex.Group)."""
        group = inkex.Group()

        # BaseElement
        group.label = group_element.name
        group.style["opacity"] = group_element.opacity
        group.style["mix-blend-mode"] = group_element.convert_blend()
        group.style["display"] = "none" if group_element.isHidden else "inline"
        if group_element.isLocked:
            group.set("sodipodi:insensitive", "true")
        if not self.has_transform_applied and group_element.localTransform is not None:
            group.transform = group_element.localTransform.convert_transform()

        # blur
        if group_element.blur > 0:
            self.set_blur(group, group_element.convert_blur())

        for child in group_element.groupElements:
            svg_element = self.load_element(child)
            if svg_element is not None:
                group.add(svg_element)

        return group

    def convert_image(self, image_element: VNImageElement) -> inkex.Image:
        """Converts a VNImageElement to an SVG image (inkex.Image)."""
        image = inkex.Image()

        # BaseElement
        image.label = image_element.name
        image.style["opacity"] = image_element.opacity
        image.style["mix-blend-mode"] = image_element.convert_blend()
        image.style["display"] = "none" if image_element.isHidden else "inline"
        if image_element.isLocked:
            image.set("sodipodi:insensitive", "true")
        if image_element.transform is not None:
            image.transform = image_element.transform
        elif not self.has_transform_applied and image_element.localTransform is not None:
            image.transform = image_element.localTransform.convert_transform()

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

    def convert_path(self, path_element: VNPathElement) -> inkex.PathElement:
        """Converts a VNPathElement to an SVG path (inkex.PathElement)."""
        path = inkex.PathElement()

        # pathGeometry
        if path_element.pathGeometries:
            for path_geometry in path_element.pathGeometries:
                path.path += path_geometry.path

        if not self.has_transform_applied and path_element.localTransform is not None:
            path.transform = path_element.localTransform.convert_transform()

            # Apply Transform
            path = inkex.PathElement.new(path.get_path().transform(path.transform))

        # PathEffect(corner), does not work for other paths in compoundPath
        if not self.has_transform_applied and path_element.pathGeometries[0].corner_radius is not None:
            corner_radius = path_element.pathGeometries[0].corner_radius
            if any(corner_radius):  # only if there are values other than 0
                self.set_corner(path, corner_radius)

        # BaseElement
        path.label = path_element.name
        path.style["opacity"] = path_element.opacity
        path.style["mix-blend-mode"] = path_element.convert_blend()
        path.style["display"] = "none" if path_element.isHidden else "inline"
        if path_element.isLocked:
            path.set("sodipodi:insensitive", "true")

        # blur
        if path_element.blur > 0:
            self.set_blur(path, path_element.convert_blur())

        # Stroke Style
        if path_element.strokeStyle is not None:
            self.set_stroke_styles(path, path_element.strokeStyle)
        else:
            path.style["stroke"] = "none"

        # Fill Style
        if path_element.fillColor is not None:
            self.set_fill_color_styles(path, path_element.fillColor)
        elif path_element.fillGradient is not None:
            # Add gradientTransform
            # matrix transform is based on Vectornator 4.13.2, format 13
            # and Linearity Curve 5.1.1, format 21
            if path_element.fillGradient.transform is not None:
                path_element.fillGradient.gradient.set("gradientTransform", path_element.fillGradient.transform)

            elif not self.has_transform_applied and path_element.localTransform is not None:
                gradient_transform = path_element.localTransform.convert_transform()
                path_element.fillGradient.gradient.set("gradientTransform", gradient_transform)

            self.set_fill_grad_styles(path, path_element.fillGradient)
        else:
            path.style["fill"] = "none"

        return path

    def convert_base(self, base_element: VNBaseElement) -> inkex.PathElement:
        """Converts a VNBaseElement to an empty SVG path (inkex.PathElement)."""
        inkex.utils.debug(f'{base_element.name}: This element will be imported as empty path.')

        path = inkex.PathElement()

        # BaseElement
        path.label = base_element.name
        path.style["opacity"] = base_element.opacity
        path.style["mix-blend-mode"] = base_element.convert_blend()
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

    def set_fill_color_styles(self, elem: inkex.BaseElement, fill: VNColor) -> None:
        """Apply fillColor to inkex.BaseElement."""
        elem.style["fill"] = fill.hex
        elem.style["fill-opacity"] = fill.alpha
        elem.style["fill-rule"] = "nonzero"

    def set_fill_grad_styles(self, elem: inkex.BaseElement, fill: VNGradient) -> None:
        """Apply fillGradient to inkex.BaseElement."""
        self.document.defs.add(fill.gradient)
        elem.style["fill"] = f"url(#{fill.gradient.get_id()})"
        # elem.style["fill-opacity"] = fill.alpha # ??
        elem.style["fill-rule"] = "nonzero"

    def set_blur(self, elem: inkex.BaseElement, blur: inkex.Filter.GaussianBlur) -> None:
        """Apply blur to inkex.BaseElement."""
        filt: inkex.Filter = inkex.Filter()
        filt.set("color-interpolation-filters", "sRGB")
        filt.add(blur)
        self.document.defs.add(filt)

        # Only one filter will be there
        elem.style["filter"] = f"url(#{filt.get_id()})"

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

    def add_guide(self, guide_element: VNBaseElement, offset: inkex.Vector2d) -> None:
        """
        Creates a Guide from VNGuideElement.

        Older Vectornator(4.10.4) uses actual path data for guides,
        which are converted into inkvn GroupElement.

        So argument type is set to VNBaseElement
        """

        def extract_guide(inkex_path: inkex.Path):
            """
            Extracts guide offset and orientation from an inkex.Path object.
            """
            path_data = inkex_path.to_arrays()

            if len(path_data) < 2:
                raise ValueError("Invalid guide path: Less than two points found.")

            (_, [x0, y0]), (_, [x1, y1]) = path_data[0], path_data[-1]

            if y0 == y1:  # horizontal
                return y0, True
            elif x0 == x1:  # vertical
                return x0, False
            else:
                raise ValueError("Invalid guide path: Not perfectly horizontal or vertical.")

        orientation = False
        guide_offset = 0

        if isinstance(guide_element, VNGuideElement):
            guide_offset = guide_element.offset
            orientation = guide_element.orientation == 1

        elif isinstance(guide_element, VNGroupElement):
            # legacy guide element.
            # there should be two elements, second one is the line
            sub_element = guide_element.groupElements[1]
            if isinstance(sub_element, VNPathElement):
                path_data = sub_element.pathGeometries[0].path
                guide_offset, orientation = extract_guide(path_data)

        if orientation:
            self.document.namedview.add_guide(guide_offset + offset.y, orient=True)
        else:
            self.document.namedview.add_guide(guide_offset + offset.x, orient=False)
