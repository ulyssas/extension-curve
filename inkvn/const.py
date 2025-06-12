"""
CURVE / VECTORNATOR MAPPING
"""

from dataclasses import dataclass
from typing import Dict, List, Union

"""
styledText, textProperty is for Newer text format (only present in Curve.)
because it's for newer text format.

textPaths in Vectornator and Linearity Curve are very different
(path contains text in Vectornator, text contains path in Linearity Curve.)

abstractImage/image cannot use this setup because
there are way too many changes between each versions
"""


@dataclass(frozen=True)
class CurveEntry:
    """
    Single entry for CURVE / VECTORNATOR mapping.

    `list` can sometimes have multiple candidades.
    """

    id: str
    list: Union[str, List[str]]


CURVE_MAPPING: Dict[str, CurveEntry] = {
    "layers": CurveEntry(id="layerIds", list="layers"),
    "guideLayer": CurveEntry(id="guideLayerId", list="layers"),
    "elements": CurveEntry(id="elementIds", list="elements"),
    "localTransform": CurveEntry(id="localTransformId", list="localTransforms"),
    "guideLine": CurveEntry(id="guideLine", list="guideLines"),
    "group": CurveEntry(id="group", list="groups"),
    "image": CurveEntry(id="image", list="images"),
    "abstractImage": CurveEntry(id="abstractImage", list="abstractImages"),
    "imageData": CurveEntry(id="abstractImage", list="abstractImages"),
    "abstractImageData": CurveEntry(id="abstractImage", list="abstractImages"),
    "stylable": CurveEntry(id="stylable", list="stylables"),
    "singleStyle": CurveEntry(id="singleStyle", list="singleStyles"),
    "abstractPath": CurveEntry(id="abstractPath", list="abstractPaths"),
    "pathData": CurveEntry(id="path", list="paths"),
    "compoundPathData": CurveEntry(id="compoundPath", list="compoundPaths"),
    "geometry": CurveEntry(id="geometryId", list="pathGeometries"),
    "subpaths": CurveEntry(id="subpathIds", list="pathGeometries"),
    "text": CurveEntry(id="abstractText", list="abstractTexts"),
    "textProperty": CurveEntry(id="text", list="texts"),
    "textPath": CurveEntry(id="textPath", list="textPaths"),
    "styledText": CurveEntry(id="textId", list="styledTexts"),
    "fill": CurveEntry(id="fillId", list="fills"),
    "strokeStyle": CurveEntry(
        id="strokeStyleId", list=["pathStrokeStyles", "strokeStyles"]
    ),
    "textStrokeStyle": CurveEntry(id="strokeStyleId", list="textStrokeStyles"),
    "brushStroke": CurveEntry(id="brushStrokeId", list="brushStrokes"),
    "brushProfile": CurveEntry(id="brushProfileId", list="brushProfiles"),
    "fillTransform": CurveEntry(id="fillTransformId", list="fillTransforms"),
}
