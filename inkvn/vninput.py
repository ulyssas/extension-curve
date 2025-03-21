"""
inkvn (extension-curve) (2025/1/21)

description: Linearity Curve / Vectornator file importer for Inkscape

! what DOESN'T work (2025/03/15): textOnPath, grid, brush stroke, marker(arrow)
! and other features I missed
"""

import os
import sys

import inkex

from inkvn.reader.read import CurveReader
from inkvn.svg.convert import CurveConverter
from inkvn.utils import to_pretty_xml

HERE = os.path.dirname(__file__) or "."
# This is suggested by https://docs.python-guide.org/writing/structure/.
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))


class CurveInput(inkex.InputExtension):
    """Open and convert .curve / .vectornator files."""

    # copied from inkaf

    def add_arguments(self, pars):
        """Add command line arguments and inx parameter."""
        pars.add_argument(
            "--clip_page",
            type=inkex.Boolean,
            dest="clip_page",
            default=False,
            help="Clip pages to hide elements outside artboards.",
        )
        pars.add_argument(
            "--pretty",
            type=inkex.Boolean,
            dest="pretty_print",
            default=False,
            help="Create an SVG file that has several lines and looks pretty to read.",
        )

    def load(self, stream):
        converter = CurveConverter()
        converter.convert(CurveReader(stream), self.options.clip_page)
        return self.svg_to_string(converter.doc.getroot())

    def svg_to_string(self, svg: inkex.SvgDocumentElement) -> bytes:
        """Convert the SvgDocumentElement to a string.

        This is mostly copied from inkex.elements._svg.SvgDocumentElement.tostring().
        """
        result = svg.tostring()
        if self.options.pretty_print:
            return to_pretty_xml(result)
        return result


def main():
    CurveInput().run()
