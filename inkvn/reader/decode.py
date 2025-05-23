"""
inkvn Unified decoder

converts both Vectornator JSON and Linearity Curve JSON data to inkvn.
This is used for Linearity Curve 5.0.x import as well (which are format 19).

Needs more Vectornator files and fileFormatVersion 30~39 for reference
"""

import base64
from typing import Any, Dict, List, Optional, Tuple, Union

import inkex

import inkvn.reader.extract as ext
import inkvn.reader.text as t
from inkvn.const import CURVE_MAPPING
from inkvn.utils import NSKeyedUnarchiver

from ..elements.artboard import Frame, VNArtboard, VNLayer
from ..elements.base import VNBaseElement, VNTransform
from ..elements.group import VNGroupElement
from ..elements.guide import VNGuideElement
from ..elements.image import VNImageElement
from ..elements.path import VNPathElement, pathGeometry
from ..elements.styles import (
    VNColor,
    VNGradient,
    basicStrokeStyle,
    pathStrokeStyle,
    styledElementData,
)
from ..elements.text import VNTextElement, singleStyledText, textProperty


class CurveDecoder:
    """
    inkvn CurveDecoder

    converts both Vectornator JSON and Linearity Curve JSON data to classes.
    """

    def __init__(self, archive: Any, gid_json: Dict, is_curve: bool) -> None:
        self.archive = archive
        self.gid_json = gid_json
        self.is_curve = is_curve
        self.artboard = self.read_artboard()

    def get_child(
        self, elem: Dict, key: str, is_curve: bool = False
    ) -> Union[Any, Dict, List[Dict], None]:
        """
        Retrieve a child attribute according to a key.

        Linearity Curve makes use of IDs and lists of elements.
        This function makes it easier to get Curve elements.
        """

        def _traverse_ids(
            ids: Any, element_list: Optional[List]
        ) -> Union[List, Any, None]:
            """pick elements specified by `ids` from `element_list`."""
            if not element_list:
                return None
            if isinstance(ids, list):
                return [element_list[i] for i in ids]
            elif isinstance(ids, int):
                return element_list[ids]
            return None

        def _find_key_in_dict(
            source: Dict, key_candidates: Union[str, List[str]]
        ) -> List[Any]:
            """
            find the list of elements from `source` dictionary,
            using multiple keys as query.
            """
            # using multiple keys as query
            if isinstance(key_candidates, list):
                for k in key_candidates:
                    if k in source:
                        return source[k]

            # using single key as query
            elif isinstance(key_candidates, str) and key_candidates in source:
                return source[key_candidates]

            return []

        try:
            # Case 1: Vectornator direct
            if not is_curve and key in elem:
                return elem[key]

            # Case 2: mapping
            mapping = CURVE_MAPPING.get(key)
            if mapping:
                # element_list contains a list of element(like `localTransforms`)
                id = elem.get(mapping.id)
                element_list = _find_key_in_dict(self.gid_json, mapping.list)
                result = _traverse_ids(id, element_list)
                if result is not None:
                    return result

            # Case 3: subElement, same key
            sub_vn = None
            if isinstance(elem.get("subElement"), dict):
                sub_vn = elem.get("subElement", {}).get(key, {}).get("_0")

            # ! Linearity Curve 5.1.2, singleStyle (the exception)
            elif key == "abstractPath" and isinstance(elem.get("subElement"), int):
                sub_vn = elem.get("subElement")

            if sub_vn is not None:
                if not is_curve:
                    return sub_vn
                # assume sub == ids
                result = _traverse_ids(sub_vn, element_list)
                if result is not None:
                    return result

            # Case 3-1: subElement, Curve key
            elif mapping is not None and isinstance(elem.get("subElement"), dict):
                sub_c = elem.get("subElement", {}).get(mapping.id, {}).get("_0")
                result = _traverse_ids(sub_c, element_list)
                if result is not None:
                    return result

            return None

        except Exception as e:
            inkex.errormsg(f"Couldn't read the child element: {e}")
            return None

    def get_child_from_id(self, list_key: str, index: int) -> Optional[Dict]:
        """Retrieve an attribute according to key and index from gid_json."""

        elements = self.gid_json.get(list_key)

        if elements is None:  # return None if the top-level key doesn't exist.
            return None

        return elements[index]

    def read_artboard(self) -> VNArtboard:
        """
        Reads gid.json(artboard) and returns artboard class.
        """
        # Layers
        artboard = self.gid_json["artboards"][0]
        layers = self.get_child(artboard, "layers", True)
        layer_list: List[VNLayer] = []
        if layers is not None:
            for layer in layers:
                layer_list.append(self.read_layer(layer))

        # Guides
        guide_layer = self.get_child(artboard, "guideLayer", True)
        guide_list: List[VNBaseElement] = []
        if isinstance(guide_layer, dict):
            guides = self.read_layer(guide_layer)
            for guide_element in guides.elements:
                if isinstance(guide_element, (VNGuideElement, VNGroupElement)):
                    guide_list.append(guide_element)

        # Background Color
        fill_color = None
        fill_gradient = None
        fill_result = self.read_fill(artboard)
        if isinstance(fill_result, VNGradient):
            fill_gradient = fill_result
        elif isinstance(fill_result, VNColor):
            fill_color = fill_result

        return VNArtboard(
            title=artboard["title"],
            frame=Frame(**artboard["frame"]),
            layers=layer_list,
            guides=guide_list,
            fillColor=fill_color,
            fillGradient=fill_gradient,
        )

    def read_layer(self, layer: Dict) -> VNLayer:
        """
        Read specified layer and return their attributes as class.

        gid_json is used for finding elements inside the layer.
        """
        elements = self.get_child(layer, "elements", True)
        element_list: List[VNBaseElement] = []
        if elements is not None:
            for element in elements:
                if element is not None:
                    element_list.append(self.read_element(element))

        return VNLayer(
            name=layer.get("name", "Unnamed Layer"),
            opacity=layer.get("opacity", 1.0),
            isVisible=layer.get("isVisible", True),
            isLocked=layer.get("isLocked", False),
            isExpanded=layer.get("isExpanded", False),
            elements=element_list,
        )

    def read_element(self, element: Dict) -> VNBaseElement:
        """Traverse specified element and extract their attributes."""
        base_element_data = {
            "name": element.get("name", "Unnamed Element"),
            "blur": element.get("blur", 0.0),
            "opacity": element.get("opacity", 1.0),
            "blendMode": element.get("blendMode", 0),
            "isHidden": element.get("isHidden", False),
            "isLocked": element.get("isLocked", False),
            "localTransform": None,
        }

        try:
            # localTransform (BaseElement)
            local_transform = self.get_child(element, "localTransform", True)
            if isinstance(local_transform, dict):
                base_element_data["localTransform"] = VNTransform(**local_transform)

            # Guide (GuideElement)
            guide = self.get_child(element, "guideLine", True)
            if isinstance(guide, dict):
                return VNGuideElement(**guide, **base_element_data)

            # Group (GroupElement)
            group = self.get_child(element, "group", True)
            if isinstance(group, dict):
                return self.read_group(group, base_element_data)

            # Image (ImageElement)
            image = self.get_child(element, "image", True)
            if isinstance(image, dict):
                return self.read_image(image, base_element_data)

            # abstractImage in Curve 5.13.0, format 40
            abs_image = self.get_child(element, "abstractImage", True)
            if isinstance(abs_image, dict):
                return self.read_image(abs_image, base_element_data)

            # Stylable (either PathElement or TextElement)
            stylable = self.get_child(element, "stylable", True)
            if isinstance(stylable, dict):
                # clipping mask
                mask = bool(stylable.get("mask", 0))

                # Stroke Style for older Curve
                stroke_style = self.read_stroke(stylable)

                # `fill` for older Curve
                # New Curve has fill/stroke inside abstractPath)
                fill_color = None
                fill_gradient = None
                abstract_path = None

                # singleStyles (based on Curve 5.1.2)
                single_style = self.get_child(stylable, "singleStyle", True)

                if isinstance(single_style, dict):
                    fill_result = self.read_fill(stylable, single_style)
                    if isinstance(fill_result, VNGradient):
                        fill_gradient = fill_result
                    elif isinstance(fill_result, VNColor):
                        fill_color = fill_result

                    # get abstract path from single_style
                    abstract_path = self.get_child(single_style, "abstractPath", True)

                # Abstract Path (PathElement)
                if abstract_path is None:
                    abstract_path = self.get_child(stylable, "abstractPath", True)

                if isinstance(abstract_path, dict):
                    path_element_data = styledElementData(
                        styled_data=abstract_path,
                        mask=mask,
                        stroke=stroke_style,
                        color=fill_color,
                        grad=fill_gradient,
                    )

                    return self.read_abs_path(path_element_data, base_element_data)

                # Abstract Text (TextElement)
                abstract_text = self.get_child(stylable, "abstractText", True)
                if isinstance(abstract_text, dict):
                    return self.read_abs_text(abstract_text, base_element_data)

            # if the element is unknown type:
            raise NotImplementedError(
                f"{base_element_data['name']}: This element has unknown type."
            )

        except Exception as e:
            inkex.errormsg(f"Error reading element: {e}")
            return VNBaseElement(**base_element_data)

    def read_group(
        self, group: Dict, base_element: Dict
    ) -> Union[VNGroupElement, VNBaseElement]:
        """Reads elements inside group and returns as VNGroupElement."""
        # get elements inside group
        group_elements = self.get_child(group, "elements", True)
        group_element_list: List[VNBaseElement] = []

        if group_elements is not None:
            for group_element in group_elements:
                if group_element is not None:
                    # get group elements recursively
                    group_element_list.append(self.read_element(group_element))

            return VNGroupElement(groupElements=group_element_list, **base_element)
        else:
            return VNBaseElement(**base_element)

    def read_image(
        self, image: Dict, base_element: Dict
    ) -> Union[VNImageElement, VNBaseElement]:
        """Reads image element, encodes image in Base64 and returns VNImageElement."""

        def _crop_rect() -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
            crop_rect = image.get("cropRect")
            if crop_rect is not None:
                assert isinstance(crop_rect, list) and len(crop_rect) == 2, (
                    f"{base_element.get('name', 'Unnamed Element')}: Invalid crop_rect."
                )
                return (
                    (float(crop_rect[0][0]), float(crop_rect[0][1])),
                    (float(crop_rect[1][0]), float(crop_rect[1][1])),
                )
            else:
                return None

        # relativePath contains *.dat (bitmap data)
        # sharedFileImage doesn't exist in 5.1.1 (file version 21) document
        # Curve 5.13.0, format 40 uses abstractImage
        # TODO format 40 crop rect is not working as expected
        image_data_id = None
        transform = None
        crop_rect = None
        encoded_image = ""

        new_image_id = image.get("imageData", {}).get("sharedFileImage", {}).get("_0")
        abs_image_id = image.get("subElement", {}).get("image", {}).get("_0")
        legacy_image_id = image.get("imageDataId")

        if new_image_id is not None:
            image_data_id = new_image_id
            crop_rect = _crop_rect()
        elif abs_image_id is not None:
            image_data_id = abs_image_id
            transform = image.get("transform")
            crop_rect = _crop_rect()
        elif legacy_image_id is not None:
            image_data_id = legacy_image_id
            transform = image.get("transform")
            crop_rect = _crop_rect()

        if isinstance(image_data_id, int):
            image_data = self.get_child_from_id("imageDatas", image_data_id)
            if image_data is not None:
                image_file = image_data["relativePath"]
                encoded_image = ext.read_dat_from_zip(self.archive, image_file)
            return VNImageElement(
                imageData=encoded_image,
                transform=transform,
                cropRect=crop_rect,
                **base_element,
            )
        else:
            return VNBaseElement(**base_element)

    def read_abs_path(
        self, path_element: styledElementData, base_element: Dict
    ) -> Union[VNPathElement, VNBaseElement]:
        """Reads path element and returns VNPathElement."""

        def _add_path(path_data: Dict, path_geometry_list: List[pathGeometry]) -> None:
            """appends path data to list"""
            geometry = self.get_child(path_data, "geometry", True)
            # Vectornator AbstractPath (direct)
            if path_data.get("nodes") is not None:
                path_geometry_list.append(
                    pathGeometry(closed=path_data["closed"], nodes=path_data["nodes"])
                )
            # SingleStyle (below geometry) and newer abstractPath
            elif isinstance(geometry, dict):
                path_geometry_list.append(
                    pathGeometry(closed=geometry["closed"], nodes=geometry["nodes"])
                )

        if path_element.styled_data is not None:
            # Stroke Style
            if path_element.stroke is None:
                path_element.stroke = self.read_stroke(path_element.styled_data)

            # fill
            if path_element.color is None and path_element.grad is None:
                fill_result = self.read_fill(path_element.styled_data)
                if isinstance(fill_result, VNGradient):
                    path_element.grad = fill_result
                elif isinstance(fill_result, VNColor):
                    path_element.color = fill_result

            # Path
            path_data = self.get_child(path_element.styled_data, "pathData", True)
            path_geometry_list: List[pathGeometry] = []
            if isinstance(path_data, dict):
                # Path Geometry
                text_path = (
                    path_data.get("subElement", {}).get("textPath", {}).get("_0")
                )
                if text_path is not None:
                    inkex.utils.debug(
                        f"{base_element['name']}: textOnPath is not supported."
                    )
                _add_path(path_data, path_geometry_list)

            # compoundPath
            compound_path_data = self.get_child(
                path_element.styled_data, "compoundPathData", True
            )
            if isinstance(compound_path_data, dict):
                # Path Geometries (subpath)
                subpaths = self.get_child(compound_path_data, "subpaths", True)
                if subpaths is not None:
                    for sub_element in subpaths:
                        _add_path(sub_element, path_geometry_list)

            return VNPathElement(
                mask=path_element.mask,
                fillColor=path_element.color,
                fillGradient=path_element.grad,
                strokeStyle=path_element.stroke,
                pathGeometries=path_geometry_list,
                **base_element,
            )
        else:
            return VNBaseElement(**base_element)

    def read_abs_text(
        self, abstract_text: Dict, base_element: Dict
    ) -> Union[VNTextElement, VNBaseElement]:
        """
        Reads Curve text element and returns VNTextElement.
        """
        # TODO Improve Text support, new format

        string = ""
        styled_text_list = []
        text_property = None
        styled_text = None

        if abstract_text is not None and abstract_text.get("attributedText") is None:
            # Which one(styledText or text) is which?
            text_prop_dict = self.get_child(abstract_text, "text", True)
            styled_text = self.get_child(abstract_text, "styledText", True)
            stroke_style_dict = self.get_child(abstract_text, "textStrokeStyle", True)

            # textPath
            text_path = self.get_child(abstract_text, "textPath", True)
            if text_path is not None:
                inkex.utils.debug(
                    f"{base_element['name']}: textOnPath is not supported."
                )

            # texts(layout??), will be named textProperty internally
            if isinstance(text_prop_dict, dict):
                text_property = textProperty(
                    textFrameLimits=text_prop_dict.get("textFrameLimits"),
                    textFramePivot=text_prop_dict.get("textFramePivot"),
                )

            # text stroke_style only contains basicStrokeStyle
            if isinstance(stroke_style_dict, dict):
                stroke_style = basicStrokeStyle(**stroke_style_dict)

            # styledTexts
            if isinstance(styled_text, dict):
                string = styled_text["string"]
                styles = t.decode_new_text(styled_text)
                styled_text_list = self.read_styled_text(styles)

            return VNTextElement(
                string=string,
                transform=None,
                styledText=styled_text_list,
                textProperty=text_property,
                **base_element,
            )

        # legacy text
        elif abstract_text is not None:
            transform = None
            text_prop_dict = self.get_child(abstract_text, "text", True)

            # I cannot replicate textProperty in legacy format
            if isinstance(text_prop_dict, dict):
                transform = text_prop_dict.get("transform")  # matrix
                # resize_mode = text_property.get("resizeMode")
                # height = text_property.get("height")
                # width = text_property.get("width")

            # styledText
            styled_text = NSKeyedUnarchiver(
                base64.b64decode(abstract_text["attributedText"])
            )
            string = styled_text["NSString"]
            styles = t.decode_old_text(styled_text)
            styled_text_list = self.read_styled_text(styles)

            return VNTextElement(
                string=string,
                transform=transform,
                styledText=styled_text_list,
                textProperty=text_property,  # TODO no text property
                **base_element,
            )
        else:
            return VNBaseElement(**base_element)

    @staticmethod
    def read_styled_text(styles: List[Dict]) -> List[singleStyledText]:
        styled_text_list: List[singleStyledText] = []
        for style in styles:
            color = None
            # color
            if style.get("fillColor") is not None:
                color = VNColor(style["fillColor"])
            # stroke # TODO text strokestyle(fix reader/text.py)
            # if style.get("strokeStyle") is not None:
            #    stroke = style["strokeStyle"]
            #    stroke = pathStrokeStyle(stroke_style, stroke)

            styled_text = singleStyledText(
                length=style["length"],
                fontName=style["fontName"],
                fontSize=style["fontSize"],
                alignment=style["alignment"],
                kerning=style.get("kerning", 0.0),
                lineHeight=style.get("lineHeight"),
                fillColor=color,
                fillGradient=None,  # TODO gradient applies globally
                strokeStyle=None,
                strikethrough=style.get("strikethrough", False),
                underline=style.get("underline", False),
            )
            styled_text_list.append(styled_text)

        return styled_text_list

    def read_stroke(self, stylable: Dict) -> Optional[pathStrokeStyle]:
        """
        Reads stroke style and returns as class.
        for newer Curve, abstractPath will be used as `stylable`.
        """
        stroke_style = self.get_child(stylable, "strokeStyle", True)
        if isinstance(stroke_style, dict):
            if (
                "dashPattern" in stroke_style
                and "join" in stroke_style
                and "cap" in stroke_style
            ):
                stroke_style["basicStrokeStyle"] = {
                    "cap": stroke_style["cap"],
                    "dashPattern": stroke_style["dashPattern"],
                    "join": stroke_style["join"],
                    "position": stroke_style["position"],
                }
            return pathStrokeStyle(
                basicStrokeStyle=basicStrokeStyle(**stroke_style["basicStrokeStyle"]),
                color=VNColor(color_dict=stroke_style["color"]),
                width=stroke_style["width"],
            )
        else:
            return None

    def read_fill(
        self, stylable: Dict, single_style: Optional[Dict] = None
    ) -> Union[VNGradient, VNColor, None]:
        """Reads fill data and returns as class."""
        # fill
        fill_data = self.get_child(stylable, "fill", True)
        color: Optional[Dict] = None
        gradient: Optional[Dict] = None

        # singleStyles (based on Curve 5.1.2)
        if single_style is not None:
            fill_data = self.get_child(single_style, "fill", True)

        if isinstance(fill_data, dict):
            color = fill_data.get("color", {}).get("_0")
            gradient = fill_data.get("gradient", {}).get("_0")

        # _process_fills
        if gradient is not None:
            # Newer Curve
            if gradient.get("transform") is not None:
                return VNGradient(
                    fill_transform=gradient["transform"],
                    transform_matrix=None,
                    stops=gradient["gradient"]["stops"],
                    typeRawValue=gradient["gradient"]["typeRawValue"],
                )
            # Old Curve like 5.1.1
            else:
                fill_transform = self.get_child(stylable, "fillTransform", True)
                assert isinstance(fill_transform, dict), "Invalid gradient."

                return VNGradient(
                    fill_transform=fill_transform,
                    transform_matrix=fill_transform["transform"],
                    stops=gradient["stops"],
                    typeRawValue=gradient["typeRawValue"],
                )
        elif color is not None:
            return VNColor(color_dict=color)
        else:
            return None
