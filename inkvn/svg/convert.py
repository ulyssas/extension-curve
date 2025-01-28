"""
Convert the intermediate data read by read.py
"""

from ..reader.datatypes import (
    Artboard, BaseElement, Color, Frame, GroupElement,
    ImageElement, Layer, PathElement, basicStrokeStyle,
    localTransform, pathStrokeStyle
)
from ..reader.read import CurveReader  # noqa: E402


class CurveConverter():
    def __init__(self) -> None:
        pass

    def convert(self, extractor: CurveReader) -> None:
        self.extractor = extractor
        self.afdoc = parse(extractor)
        self.doc = SvgOutputMixin.get_template(
            width=self.afdoc["DocR"].get("DfSz", (100, 100))[0],
            height=self.afdoc["DocR"].get("DfSz", (100, 100))[1],
            unit="px",
        )
        self.document = self.doc.getroot()
        root_chlds = self.afdoc["DocR"].get("Chld", [])
        assert len(root_chlds) <= 1
        if root_chlds:
            self._parse_doc(root_chlds[0])

        if "DCMD" in self.afdoc["DocR"] and "FlNm" in self.afdoc["DocR"]["DCMD"]:
            title = self.afdoc["DocR"]["DCMD"]["FlNm"]
            title = (
                title[: -len(".afdesign")
                      ] if title.endswith(".afdesign") else title
            ) + ".svg"
            self.document.add(inkex.Title.new(title))
