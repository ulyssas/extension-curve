"""
VI decoders

converts Linearity Curve (5.18) JSON data to inkvn.

Only tested for fileFormatVersion 44.

TODO: Adapt to datatypes.py
"""

from typing import Any, Dict, List

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
        # TODO: Add support for older files
        image = get_json_element(gid_json, "images", image_id)["imageData"]["sharedFileImage"]["_0"]
        image_file = get_json_element(gid_json, "imageDatas", image)["relativePath"]
        image_data = ext.read_dat_from_zip(archive, image_file)
        return ImageElement(imageData=image_data, **base_element_data)

    # Stylable (either PathElement or TextElement)
    stylable_id = element.get("subElement", {}).get("stylable", {}).get("_0")
    if stylable_id is not None:
        stylable = get_json_element(gid_json, "stylables", stylable_id)

        # Abstract Path (PathElement)
        abstract_path_id = stylable.get("subElement", {}).get("abstractPath", {}).get("_0")
        if abstract_path_id is not None:
            abstract_path = get_json_element(gid_json, "abstractPaths", abstract_path_id)

            # will be used to return PathElement
            fill = None
            fill_id = None
            stroke_style = None

            # Stroke Style
            stroke_style_id = abstract_path.get("strokeStyleId")
            if stroke_style_id is not None:
                stroke_style = get_json_element(gid_json, "pathStrokeStyles", stroke_style_id)
                stroke_style = pathStrokeStyle(
                    basicStrokeStyle=basicStrokeStyle(**stroke_style["basicStrokeStyle"]),
                    color=Color(color_dict=stroke_style["color"]),
                    width=stroke_style["width"]
                )

            # fill
            fill_id = abstract_path.get("fillId")
            if fill_id is not None:
                gradient = get_json_element(gid_json, "fills", fill_id).get("gradient", {}).get("_0")
                color: Dict = get_json_element(gid_json, "fills", fill_id).get("color", {}).get("_0")

                if gradient is not None:
                    # raise NotImplementedError("Gradient is not supported.")
                    pass
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
                # TODO: pathGeometry should be classes
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
                pathGeometry=path_geometry_list,
                **base_element_data
            )

        # Abstract Text (TextElement)
        abstract_text_id = stylable.get("subElement", {}).get("abstractText", {}).get("_0")
        if abstract_text_id is not None:
            raise NotImplementedError("Text is not supported.")
        #     abstract_text = get_json_element(gid_json, "abstractTexts", abstract_text_id)
        #     text_id = abstract_text["textId"]
        #     styled_text_id = abstract_text["subElement"]["text"]["_0"]

        #     # texts(layout??), will be named textProperty internally
        #     if text_id is not None:
        #         element_result["textProperty"] = get_json_element(gid_json, "texts", text_id)

        #     # styledTexts
        #     if styled_text_id is not None:
        #         element_result["styledText"] = get_json_element(gid_json, "styledTexts", styled_text_id)

        #! singleStyle (NON-EXISTENT in latest format, found in fileVersion 21)
        #single_style_id = stylable["subElement"]["singleStyle"]["_0"]
        #if single_style_id is not None:
        #    single_style = get_json_element(gid_json, "singleStyles", single_style_id)
        #    element_result["singleStyle"] = single_style
        #    # TODO Add singleStyles support later

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


def vectornator_to_artboard(gid_json):
    """Reads Vectornator gid.json and returns Curve artboard."""
    return {
        "title": gid_json.get("title", "Untitled"),
        "activeLayerIndex": gid_json.get("activeLayerIndex", 0),
        "frame": gid_json.get("frame", {}),
        "gid": gid_json.get("gid", "")
    }


def get_json_element(gid_json: Dict, list_key: str, index: int) -> Any:
    """Get an attribute according to key and index from gid_json."""
    elements = gid_json[list_key]
    return elements[index]

