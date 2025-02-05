"""
inkvn (extension-curve) (2025/1/21)

description: Linearity Curve file importer with fileVersion 44

! what DOESN'T work (2025/02/05): Gradient, Blur, Text, mask, guide
"""

import os
import sys

import inkex

HERE = os.path.dirname(__file__) or "."
# This is suggested by https://docs.python-guide.org/writing/structure/.
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))


from inkvn.reader.read import CurveReader
from inkvn.svg.convert import CurveConverter


class CurveInput(inkex.InputExtension):
    """
    Open and convert Linearity Curve (.curve) files.

    Vectornator (.vectornator) file is not supported.

    You can upgrade file format by opening vectornator file in Linearity Curve, then export as .curve.
    """

    # copied from inkaf
    def load(self, stream):
        converter = CurveConverter()
        converter.convert(CurveReader(stream))
        return converter.doc


def main():
    CurveInput().run()
