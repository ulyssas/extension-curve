"""
Convert the intermediate data read by read.py
"""

import inkex
import lxml.etree

from inkvn.reader.datatypes import (
    Artboard, BaseElement, Color, Frame, GroupElement,
    ImageElement, Layer, PathElement, basicStrokeStyle,
    localTransform, pathGeometry, pathStrokeStyle
)
from inkvn.reader.read import CurveReader  # noqa: E402


class CurveConverter():
    def __init__(self) -> None:
        self.reader: CurveReader
        self.doc: lxml.etree._ElementTree
        self.document: inkex.SvgDocumentElement

    def convert(self, reader: CurveReader) -> None:
        self.reader = reader
        
        if not doc:
            doc = self.get_template(
                width=artboard["frame"]["width"],
                height=artboard["frame"]["height"],
            )
        svg = doc.getroot()
        page = inkex.Page.new(
            width=artboard["frame"]["width"],
            height=artboard["frame"]["height"],
            x=artboard["frame"]["x"],
            y=artboard["frame"]["y"],
        )
        svg.namedview.add(page)
        page.set("inkscape:label", artboard["title"])
        self.load_page(
            svg.add(inkex.Layer.new(artboard["title"])), artboard
        )
        # TODO Grids are per artboard, not global
        doc.getroot()

