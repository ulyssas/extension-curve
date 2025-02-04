"""
VI decoders

converts Linearity Curve (5.18) JSON data to inkvn.

Only tested for fileFormatVersion 44.
"""

from typing import Any, Dict, List, Optional

import inkex

import inkvn.reader.extract as ext
from inkvn.reader.datatypes import (
    Artboard, BaseElement, Color, Frame, GroupElement,
    ImageElement, Layer, PathElement, basicStrokeStyle,
    localTransform, pathGeometry, pathStrokeStyle
)


def read_artboard(archive: Any, gid_json: Dict) -> Artboard:
    """
    Reads gid.json(artboard) and returns artboard class.

    Argument `archive` is needed for image embedding.
    """
    # "layer_ids" contain layer indexes, while "layers" contain existing layers
    artboard = gid_json["artboards"][0] # ? format version sensitive????
    layer_ids = artboard["layerIds"]
    layer_list: List[Layer] = []

    # Locate elements specified in layers.elementIds with read_layer
    for layer_id in layer_ids:
        layer = get_json_element(gid_json, "layers", layer_id)
        layer_list.append(read_layer(archive, gid_json, layer))

    return Artboard(
        title=artboard["title"],
        frame=Frame(**artboard["frame"]),
        layers=layer_list
    )


def read_layer(archive: Any, gid_json: Dict, layer: Dict) -> Layer:
    """
    Read specified layer and return their attributes as class.

    gid_json is used for finding elements inside the layer.
    """
    layer_element_ids = layer["elementIds"]
    element_list: List[BaseElement] = []

    # process each elements
    for element_id in layer_element_ids:
        element = get_json_element(gid_json, "elements", element_id)
        if element is not None:
            element_list.append(read_element(archive, gid_json, element))

    return Layer(
        name=layer["name"],
        opacity=layer["opacity"],
        isVisible=layer["isVisible"],
        isLocked=layer["isLocked"],
        isExpanded=layer["isExpanded"],
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
    local_transform_id = element["localTransformId"]
    if local_transform_id is not None:
        base_element_data["localTransform"] = localTransform(
            **get_json_element(gid_json, "localTransforms", local_transform_id)
        )

    # Image (ImageElement)
    image_id = element.get("subElement", {}).get("image", {}).get("_0")
    if image_id is not None:
        # relativePath contains *.dat (bitmap data)
        # sharedFileImage doesn't exist in 5.1.1 (file version 21) document
        image = get_json_element(gid_json, "images", image_id)
        transform = None

        image_data_id = image.get("imageData", {}).get("sharedFileImage", {}).get("_0")
        if image_data_id is None: # legacy image
            image_data_id = image.get("imageDataId")
            transform = image.get("transform")

        image_file = get_json_element(gid_json, "imageDatas", image_data_id)["relativePath"]
        image_data = ext.read_dat_from_zip(archive, image_file)
        return ImageElement(imageData=image_data, transform=transform, **base_element_data)

    # Stylable (either PathElement or TextElement)
    stylable_id = element.get("subElement", {}).get("stylable", {}).get("_0")
    if stylable_id is not None:
        stylable = get_json_element(gid_json, "stylables", stylable_id)

        # will be used to return PathElement
        fill = None
        fill_id = None
        stroke_style = None
        stroke_style_id = None
        abstract_path_id = None

        # ! singleStyles compatibility (NOT TESTED AT ALL), based on Curve 5.1.2
        single_style_id = stylable.get("subElement", {}).get("singleStyle", {}).get("_0")
        if single_style_id is not None:
            single_style = get_json_element(gid_json, "singleStyles", single_style_id)
            # old abstractPath lacks these ids
            stroke_style_id = stylable.get("strokeStyleId")
            fill_id = single_style.get("fillId")
            abstract_path_id = single_style.get("subElement")

        # Abstract Path (PathElement)
        sub_element = stylable.get("subElement", {})
        if "abstractPath" in sub_element:
            abstract_path_id = sub_element["abstractPath"].get("_0")
        if abstract_path_id is not None:
            abstract_path = get_json_element(gid_json, "abstractPaths", abstract_path_id)

            # Stroke Style
            if "strokeStyleId" in abstract_path:
                stroke_style_id = abstract_path["strokeStyleId"]
            if stroke_style_id is not None:
                stroke_style = get_json_element(gid_json, "pathStrokeStyles", stroke_style_id)

                if stroke_style is None:  # Try legacy "strokeStyles" if not found
                    stroke_style = get_json_element(gid_json, "strokeStyles", stroke_style_id)

                if "dashPattern" in stroke_style and "join" in stroke_style and "cap" in stroke_style:
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
            if "fillId" in abstract_path:
                fill_id = abstract_path["fillId"]
            if fill_id is not None:
                gradient = get_json_element(gid_json, "fills", fill_id).get("gradient", {}).get("_0")
                color: Dict = get_json_element(gid_json, "fills", fill_id).get("color", {}).get("_0")

                if gradient is not None:
                    # TODO Add support for Gradient
                    inkex.utils.debug(f'{base_element_data["name"]}: Gradient is not supported and will be ignored.')
                elif color is not None:
                    fill = Color(color_dict=color)

            # Path
            path_id = abstract_path.get("subElement", {}).get("path", {}).get("_0")
            path_geometry_list: List[pathGeometry] = []
            if path_id is not None:
                path = get_json_element(gid_json, "paths", path_id)

                # Path Geometry
                geometry_id = path["geometryId"]
                if geometry_id is not None:
                    path_geometry = pathGeometry(
                        **get_json_element(gid_json, "pathGeometries", geometry_id)
                    )
                    path_geometry_list.append(path_geometry)

            # compoundPath
            compound_path_id = abstract_path.get("subElement", {}).get("compoundPath", {}).get("_0")
            if compound_path_id is not None:
                compound_path = get_json_element(gid_json, "compoundPaths", compound_path_id)

                # Path Geometries (subpath)
                subpath_ids = compound_path.get("subpathIds")
                if subpath_ids is not None:
                    for id in subpath_ids:
                        path_geometry = pathGeometry(
                            **get_json_element(gid_json, "pathGeometries", id)
                        )
                        path_geometry_list.append(path_geometry)

            return PathElement(
                fill=fill,
                fillId=fill_id,
                strokeStyle=stroke_style,
                pathGeometries=path_geometry_list,
                **base_element_data
            )

        # Abstract Text (TextElement)
        abstract_text_id = stylable.get("subElement", {}).get("abstractText", {}).get("_0")
        if abstract_text_id is not None:
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
    group_id = element.get("subElement", {}).get("group", {}).get("_0")
    if group_id is not None:
        # get elements inside group
        group = get_json_element(gid_json, "groups", group_id)
        group_element_ids = group["elementIds"]
        group_element_list: List[BaseElement] = []

        for group_element_id in group_element_ids:
            group_element = get_json_element(gid_json, "elements", group_element_id)
            if group_element:
                # get group elements recursively
                group_element_list.append(read_element(archive, gid_json, group_element))

        return GroupElement(groupElements=group_element_list, **base_element_data)

    # if the element is unknown type:
    return BaseElement(**base_element_data)


def get_json_element(json_data: Dict, list_key: str, index: str) -> Optional[Dict]:
    """Retrieve an attribute according to key and index from gid_json."""

    elements = json_data.get(list_key)

    if elements is None: # return None if the top-level key doesn't exist.
        return None

    return elements[index]
