"""
VI decoders

converts Vectornator JSON data to inkvn (Vectornator mode).
This is used for Linearity Curve 5.0.x import as well (format 19).

Needs more Vectornator files for reference
"""

from typing import Any, Dict, List

import inkex

import inkvn.reader.extract as ext
from inkvn.elements.artboard import VNArtboard

from ..elements.artboard import VNArtboard, VNLayer, Frame
from ..elements.base import VNBaseElement, VNTransform
from ..elements.guide import VNGuideElement
from ..elements.group import VNGroupElement
from ..elements.image import VNImageElement
from ..elements.path import VNPathElement, pathGeometry
from ..elements.text import VNTextElement, styledText, textProperty
from ..elements.styles import VNColor, VNGradient, pathStrokeStyle, basicStrokeStyle


def read_vn_artboard(archive: Any, gid_json: Dict) -> VNArtboard:
    """
    Reads gid.json(artboard) and returns artboard class.

    Argument `archive` is needed for image embedding.
    """
    # Layers
    layers = gid_json["layers"]
    layer_list: List[VNLayer] = []
    for layer in layers:
        if layer is not None:
            layer_list.append(read_vn_layer(archive, layer))

    # Guides
    guides = gid_json["guideLayer"]["elements"]
    guide_list: List[VNGuideElement] = []
    for guide in guides:
        if guide is not None:
            guide_list.append(read_vn_element(archive, guide))

    # Background Color
    # gid_json["fillGradient"] and gid_json["fillColor"] is not confirmed
    fill_gradient = None
    fill_color = None
    fill_result = read_vn_fill(gid_json)
    if isinstance(fill_result, VNGradient):
        fill_gradient = fill_result
    elif isinstance(fill_result, VNColor):
        fill_color = fill_result

    return VNArtboard(
        title=gid_json["title"],
        frame=Frame(**gid_json["frame"]),
        layers=layer_list,
        guides=guide_list,
        fillColor=fill_color,
        fillGradient=fill_gradient
    )


def read_vn_layer(archive: Any, layer: Dict) -> VNLayer:
    """
    Read specified layer and return their attributes as class.
    """
    elements = layer["elements"]
    element_list: List[VNBaseElement] = []
    for element in elements:
        if element is not None:
            element_list.append(read_vn_element(archive, element))

    # properties
    if layer.get("properties") is not None:
        properties = layer["properties"]
        return VNLayer(
            name=properties.get("name"),
            opacity=properties.get("opacity"),
            isVisible=properties.get("isVisible"),
            isLocked=properties.get("isLocked"),
            isExpanded=properties.get("isExpanded"),
            elements=element_list
        )
    # properties did not exist in 4.9.0, format 7.
    else:
        return VNLayer(
            name=layer.get("name"),
            opacity=layer.get("opacity"),
            isVisible=layer.get("isVisible"),
            isLocked=layer.get("isLocked"),
            isExpanded=layer.get("isExpanded"),
            elements=element_list
        )


def read_vn_element(archive: Any, element: Dict) -> VNBaseElement:
    """Traverse specified element and extract their attributes."""
    base_element_data = {
        "name": element.get("name", "Unnamed Element"),
        "blur": element.get("blur", 0.0),
        "opacity": element.get("opacity", 1.0),
        "blendMode": element.get("blendMode", 0),
        "isHidden": element.get("isHidden", False),
        "isLocked": element.get("isLocked", False),
        "localTransform": None
    }

    # localTransform (BaseElement)
    local_transform = element.get("localTransform")
    if local_transform is not None:
        base_element_data["localTransform"] = VNTransform(
            **local_transform
        )

    # Image (ImageElement)
    image = element.get("subElement", {}).get("image", {}).get("_0")
    if image is not None:
        return read_vn_image(archive, image, base_element_data)

    # Stylable (either PathElement or TextElement)
    stylable = element.get("subElement", {}).get("stylable", {}).get("_0")
    if stylable is not None:
        # clipping mask
        mask = stylable.get("mask", 0)

        # Stroke Style
        stroke_style = read_vn_stroke(stylable)

        # fill
        fill_gradient = None
        fill_color = None
        fill_result = read_vn_fill(stylable)
        if isinstance(fill_result, VNGradient):
            fill_gradient = fill_result
        elif isinstance(fill_result, VNColor):
            fill_color = fill_result

        # singleStyles (Vectornator 4.13.6, format 19)
        abstract_path = None
        single_style = stylable.get("subElement", {}).get("singleStyle", {}).get("_0")
        if single_style is not None:
            fill_data = single_style.get("fill")
            if fill_data is not None:
                color: Dict = fill_data.get("color", {}).get("_0")
                gradient: Dict = fill_data.get("gradient", {}).get("_0")
                if gradient is not None:
                    fill_gradient = VNGradient(
                        start_end=stylable["fillTransform"],
                        transform_matrix=stylable["fillTransform"]["transform"],
                        stops=gradient["stops"],
                        typeRawValue=gradient["typeRawValue"]
                    )
                elif color is not None:
                    fill_color = VNColor(color_dict=color)

            # use single_style as abstract path
            abstract_path = single_style.get("subElement")

        # Abstract Path (PathElement)
        sub_element = stylable.get("subElement", {})
        if "abstractPath" in sub_element:
            abstract_path = sub_element["abstractPath"].get("_0")
        if abstract_path is not None:
            path_element_data = {
                "abst_path": abstract_path,
                "mask": mask,
                "stroke": stroke_style,
                "color": fill_color,
                "grad": fill_gradient,
            }
            return read_vn_abst_path(path_element_data, base_element_data)

        # Abstract Text (TextElement)
        text_data = stylable.get("subElement", {}).get("text", {}).get("_0")
        if text_data is not None:
            # TODO Add support for Vectornator Text
            inkex.utils.debug(
                f'{base_element_data["name"]}: Vectornator Text is not supported and will be ignored.')
        #     abstract_text = get_json_element(gid_json, "abstractTexts", abstract_text_id)
        #     text_id = abstract_text["textId"]
        #     styled_text_id = abstract_text["subElement"]["text"]["_0"]

        #     # texts(layout??), will be named textProperty internally
        #     if text_id is not None:
        #         element_result["textProperty"] = get_json_element(gid_json, "texts", text_id)

        #     # styledTexts
        #     if styled_text_id is not None:
        #         element_result["styledText"] = get_json_element(gid_json, "styledTexts", styled_text_id)

    # Group (GroupElement)
    group = element.get("subElement", {}).get("group", {}).get("_0")
    if group is not None:
        return read_vn_group(archive, group, base_element_data)

    # Guide (GuideElement)
    guide = element.get("subElement", {}).get("guideLine", {}).get("_0")
    if guide is not None:
        return VNGuideElement(**guide, **base_element_data)

    # if the element is unknown type:
    return VNBaseElement(**base_element_data)


def read_vn_image(archive: Any, image: Dict, base_element: Dict) -> VNImageElement:
    # relativePath contains *.dat (bitmap data)
    # sharedFileImage doesn't exist in 5.1.1 (file version 21) document
    transform = image["transform"]
    image_file = image["imageData"]["relativePath"]
    image_data = ext.read_dat_from_zip(archive, image_file)
    return VNImageElement(imageData=image_data, transform=transform, **base_element)


def read_vn_abst_path(path_element: Dict, base_element: Dict) -> VNPathElement:

    def add_path(path_data: Dict, path_geometry_list: List[pathGeometry]) -> None:
        """appends path data to list"""
        geometry = path_data.get("geometry")
        # AbstractPath
        if path_data.get("nodes") is not None:
            # Path Geometry
            path_geometry_list.append(
                pathGeometry(
                    closed=path_data["closed"],
                    nodes=path_data["nodes"]
                )
            )
        # SingleStyle
        elif geometry is not None:
            path_geometry_list.append(
                pathGeometry(
                    closed=geometry["closed"],
                    nodes=geometry["nodes"]
                )
            )

    # Path
    path_data = path_element["abst_path"].get("subElement", {}).get("pathData", {}).get("_0")
    path_geometry_list: List[pathGeometry] = []

    if path_data is not None:
        add_path(path_data, path_geometry_list)

    # compoundPath
    compound_path_data = path_element["abst_path"].get("subElement", {}).get("compoundPathData", {}).get("_0")
    if compound_path_data is not None:
        # Path Geometries (subpath)
        subpaths = compound_path_data.get("subpaths")
        if subpaths is not None:
            for sub_element in subpaths:
                sub_stylable = sub_element.get(
                    "subElement", {}).get("stylable", {}).get("_0")
                # Vectornator 4.13.5, format 16
                if sub_stylable is not None:
                    # ! this "abstractPath" could be singleStyle
                    # ! I need more Vectornator document to confirm this
                    sub_path = sub_stylable["subElement"]["abstractPath"]["_0"]["subElement"]["pathData"]["_0"]

                # else (Vectornator 4.13.6, format 19)
                else:
                    sub_path = sub_element

                add_path(sub_path, path_geometry_list)

    return VNPathElement(
        mask=path_element["mask"],
        fillColor=path_element["color"],
        fillGradient=path_element["grad"],
        strokeStyle=path_element["stroke"],
        pathGeometries=path_geometry_list,
        **base_element
    )


def read_vn_group(archive: Any, group: Dict, base_element: Dict) -> VNGroupElement:
    # get elements inside group
    group_elements = group["elements"]
    group_element_list: List[VNBaseElement] = []

    for group_element in group_elements:
        if group_element is not None:
            # get group elements recursively
            group_element_list.append(
                read_vn_element(archive, group_element))

    return VNGroupElement(groupElements=group_element_list, **base_element)


def read_vn_stroke(stylable: Dict) -> pathStrokeStyle:
    stroke_style = stylable.get("strokeStyle")
    if stroke_style is not None:
        stroke_style["basicStrokeStyle"] = {
            "cap": stroke_style["cap"],
            "dashPattern": stroke_style["dashPattern"],
            "join": stroke_style["join"],
            "position": stroke_style["position"]
        }
        return pathStrokeStyle(
            basicStrokeStyle=basicStrokeStyle(
                **stroke_style["basicStrokeStyle"]),
            color=VNColor(color_dict=stroke_style["color"]),
            width=stroke_style["width"]
        )


def read_vn_fill(stylable: Dict) -> VNGradient | VNColor | None:
    # fill
    fill_data = stylable.get("fill")
    fill_color = stylable.get("fillColor")
    fill_gradient = stylable.get("fillGradient")

    # Vectornator 4.13.2, format 13
    if fill_data is not None:
        gradient: Dict = fill_data.get("gradient", {}).get("_0")
        color: Dict = fill_data.get("color", {}).get("_0")
        if gradient is not None:
            return VNGradient(
                start_end=stylable["fillTransform"],
                transform_matrix=stylable["fillTransform"]["transform"],
                stops=gradient["stops"],
                typeRawValue=gradient["typeRawValue"]
            )
        elif color is not None:
            return VNColor(color_dict=color)

    # Vectornator 4.10.4, format 8
    elif fill_color is not None or fill_gradient is not None:
        if fill_gradient is not None:
            # inkex.utils.debug(f'{base_element_data["name"]}: Gradient is not supported and will be ignored.')
            return VNGradient(
                start_end=stylable["fillTransform"],
                transform_matrix=stylable["fillTransform"]["transform"],
                stops=fill_gradient["stops"],
                typeRawValue=fill_gradient["typeRawValue"]
            )
        elif fill_color is not None:
            return VNColor(color_dict=fill_color)
