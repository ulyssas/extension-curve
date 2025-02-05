"""
VI decoders

converts Vectornator JSON data to inkvn.

Needs more Vectornator files for reference
"""

from typing import Any, Dict, List

import inkex

import inkvn.reader.extract as ext
from inkvn.reader.datatypes import (
    Artboard, BaseElement, Color, Frame, GroupElement, Gradient,
    ImageElement, Layer, PathElement, basicStrokeStyle,
    localTransform, pathGeometry, pathStrokeStyle
)


def read_artboard(archive: Any, gid_json: Dict) -> Artboard:
    """
    Reads gid.json(artboard) and returns artboard class.

    Argument `archive` is needed for image embedding.
    """
    layers = gid_json["layers"]
    layer_list: List[Layer] = []

    for layer in layers:
        layer_list.append(read_layer(archive, gid_json, layer))

    return Artboard(
        title=gid_json["title"],
        frame=Frame(**gid_json["frame"]),
        layers=layer_list
    )


def read_layer(archive: Any, gid_json: Dict, layer: Dict) -> Layer:
    """
    Read specified layer and return their attributes as class.

    gid_json is used for finding elements inside the layer.
    """
    properties = layer["properties"]
    elements = layer["elements"]
    element_list: List[BaseElement] = []

    # process each elements
    for element in elements:
        if element is not None:
            element_list.append(read_element(archive, gid_json, element))

    return Layer(
        name=properties["name"],
        opacity=properties["opacity"],
        isVisible=properties["isVisible"],
        isLocked=properties["isLocked"],
        isExpanded=properties["isExpanded"],
        elements=element_list
    )


def read_element(archive, gid_json, element) -> BaseElement:
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
    if local_transform:
        base_element_data["localTransform"] = localTransform(
            **local_transform
        )

    # Image (ImageElement)
    image = element.get("subElement", {}).get("image", {}).get("_0")
    if image is not None:
        # relativePath contains *.dat (bitmap data)
        # sharedFileImage doesn't exist in 5.1.1 (file version 21) document
        transform = image["transform"]
        image_file = image["imageData"]["relativePath"]
        image_data = ext.read_dat_from_zip(archive, image_file)
        return ImageElement(imageData=image_data, transform=transform, **base_element_data)

    # Stylable (either PathElement or TextElement)
    stylable = element.get("subElement", {}).get("stylable", {}).get("_0")
    if stylable is not None:
        # Stroke Style
        stroke_style = stylable.get("strokeStyle")
        if stroke_style is not None:
            stroke_style["basicStrokeStyle"] = {
                "cap": stroke_style["cap"],
                "dashPattern": stroke_style["dashPattern"],
                "join": stroke_style["join"],
                "position": stroke_style["position"]
            }
            stroke_style = pathStrokeStyle(
                basicStrokeStyle=basicStrokeStyle(**stroke_style["basicStrokeStyle"]),
                color=Color(color_dict=stroke_style["color"]),
                width=stroke_style["width"]
            )

        # fill
        fill_color = None
        fill_gradient = None
        fill_data = stylable.get("fill")
        fill_color = stylable.get("fillColor")
        fill_gradient = stylable.get("fillGradient")
        if fill_data:
            gradient: Dict = fill_data.get("gradient", {}).get("_0")
            color: Dict = fill_data.get("color", {}).get("_0")

            # Vectornator 4.13.2, format 13
            if gradient is not None:
                fill_gradient = Gradient(
                    start_end=stylable["fillTransform"],
                    transform_matrix=stylable["fillTransform"]["transform"],
                    stops=gradient["stops"],
                    typeRawValue=gradient["typeRawValue"]
                )
            elif color:
                fill_color = Color(color_dict=color)

        # Vectornator 4.10.4, format 8
        elif fill_color or fill_gradient:
            if fill_gradient:
                #inkex.utils.debug(f'{base_element_data["name"]}: Gradient is not supported and will be ignored.')
                fill_gradient = Gradient(
                    start_end=stylable["fillTransform"],
                    transform_matrix=stylable["fillTransform"]["transform"],
                    stops=fill_gradient["stops"],
                    typeRawValue=fill_gradient["typeRawValue"]
                )
            elif fill_color:
                fill_color = Color(color_dict=fill_color)

        # singleStyles (Vectornator 4.13.6, format 19)
        abstract_path = None
        single_style = stylable.get("subElement", {}).get("singleStyle", {}).get("_0")
        if single_style is not None:
            fill_data = single_style.get("fill")
            if fill_data:
                color: Dict = fill_data.get("color", {}).get("_0")
                gradient: Dict = fill_data.get("gradient", {}).get("_0")

                if gradient is not None:
                    fill_gradient = Gradient(
                        start_end=stylable["fillTransform"],
                        transform_matrix=stylable["fillTransform"]["transform"],
                        stops=gradient["stops"],
                        typeRawValue=gradient["typeRawValue"]
                    )
                elif color:
                    fill_color = Color(color_dict=color)

            # use single_style as abstract path
            abstract_path = single_style.get("subElement")

        # Abstract Path (PathElement)
        path_geometry_list: List[pathGeometry] = []
        sub_element = stylable.get("subElement", {})
        if "abstractPath" in sub_element:
            abstract_path = sub_element["abstractPath"].get("_0")
        if abstract_path is not None:
            # Path
            path_data = abstract_path.get("subElement", {}).get("pathData", {}).get("_0")
            if path_data is not None:
                geometry = path_data.get("geometry")

                # AbstractPath
                if path_data.get("nodes"):
                    # Path Geometry
                    path_geometry = pathGeometry(
                        closed=path_data["closed"],
                        nodes=path_data["nodes"]
                    )
                    path_geometry_list.append(path_geometry)
                # SingleStyle
                elif geometry:
                    path_geometry = pathGeometry(
                        closed=geometry["closed"],
                        nodes=geometry["nodes"]
                    )
                    path_geometry_list.append(path_geometry)

            # compoundPath
            compound_path_data = abstract_path.get("subElement", {}).get("compoundPathData", {}).get("_0")
            if compound_path_data is not None:
                # Path Geometries (subpath)
                subpaths = compound_path_data.get("subpaths")
                if subpaths is not None:
                    for sub_element in subpaths:
                        # ! this "abstractPath" could be singleStyle
                        # ! I need more Vectornator document to confirm this
                        sub_stylable = sub_element.get("subElement", {}).get("stylable", {}).get("_0")
                        if sub_stylable is not None:
                            sub_path = sub_stylable["subElement"]["abstractPath"]["_0"]["subElement"]["pathData"]["_0"]

                        # else (Vectornator 4.13.6, format 19)
                        else:
                            sub_path = sub_element

                        path_geometry = pathGeometry(
                            closed=sub_path["closed"],
                            nodes=sub_path["nodes"]
                        )
                        path_geometry_list.append(path_geometry)

            return PathElement(
                fillColor=fill_color,
                fillGradient=fill_gradient,
                strokeStyle=stroke_style,
                pathGeometries=path_geometry_list,
                **base_element_data
            )

        # Abstract Text (TextElement)
        text_data = stylable.get("subElement", {}).get("text", {}).get("_0")
        if text_data is not None:
            # TODO Add support for Text
            inkex.utils.debug(f'{base_element_data["name"]}: Text is not supported and will be ignored.')
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
        # get elements inside group
        group_elements = group["elements"]
        group_element_list: List[BaseElement] = []

        for group_element in group_elements:
            if group_element:
                # get group elements recursively
                group_element_list.append(read_element(archive, gid_json, group_element))

        return GroupElement(groupElements=group_element_list, **base_element_data)

    # if the element is unknown type:
    return BaseElement(**base_element_data)

