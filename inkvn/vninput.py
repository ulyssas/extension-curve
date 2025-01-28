"""
inkvn (extension-curve) (2025/1/21)

description: Linearity Curve file importer with fileVersion 44

what works (2025/01/23): None
"""

import os
import sys

import inkex


HERE = os.path.dirname(__file__) or "."
# This is suggested by https://docs.python-guide.org/writing/structure/.
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))


from inkvn.reader.read import VNReader  # noqa: E402
from inkvn.svg.convert import VNConverter  # noqa: E402


class CurveInput(inkex.InputExtension):
    """
    Open and convert Linearity Curve (.curve) files.

    Vectornator (.vectornator) file is not supported.

    You can upgrade file format by opening vectornator file in Linearity Curve, then export as .curve.
    """

    def load(self, stream):
        converter = VNConverter()
        converter.convert(VNReader(stream))
        return converter.doc.getroot()


def main():
    CurveInput().run()
