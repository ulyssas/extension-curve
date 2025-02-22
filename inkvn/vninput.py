"""
inkvn (extension-curve) (2025/1/21)

description: Linearity Curve / Vectornator file importer for Inkscape

! what DOESN'T work (2025/02/15): Text, grid, brush stroke, marker(arrow)
! and other features I missed
"""

from .svg.convert import CurveConverter
from .reader.read import CurveReader
import os
import sys

import inkex

HERE = os.path.dirname(__file__) or "."
# This is suggested by https://docs.python-guide.org/writing/structure/.
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))


class CurveInput(inkex.InputExtension):
    """Open and convert .curve and .vectornator files."""

    # copied from inkaf
    def load(self, stream):
        converter = CurveConverter()
        converter.convert(CurveReader(stream))
        return converter.doc


def main():
    CurveInput().run()
