"""
inkvn Reader

Reads Linearity Curve files and convert them into intermediate data.
"""


import logging
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List

from packaging import version

import decode as d
import extract as ext
from datatypes import (
    Artboard, BaseElement, Color, Frame, GroupElement,
    ImageElement, Layer, PathElement, basicStrokeStyle,
    localTransform, pathStrokeStyle
)


class CurveReader:
    """
    inkvn CurveReader

    A Linearity Curve file reader to convert Curve documents to dataclasses.
    """
    def __init__(self, stream):
        self.archive = zipfile.ZipFile(stream, 'r')
        self.artboards: List[Artboard] = []

        self.read()

    def read(self):
        manifest = ext.extract_manifest(self.archive)
        document = ext.extract_document(self.archive, manifest)
        drawing_data = ext.extract_drawing_data(document)

        units = drawing_data.get("settings", {}).get("units", "Pixels")
        version = document.get("appVersion", "unknown app version")
        artboard_paths = drawing_data.get("artboardPaths", [])

        # will be used later (as Inkscape attribute)
        print(f"Unit: {units}")

        if not artboard_paths:
            raise ValueError("No artboard paths found in the document.")

        # Step 5: Read Artboard (GUID JSON)
        # If there's multiple artboards, only the first will be exported.
        gid_json = ext.extract_gid_json(self.archive, artboard_paths[0])

        # if the file is Linearity Curve
        if self._check_if_curve(version):
            print(f"Supported version: {version}.")

            # TODO: loading function should be here
            artboard = gid_json.get("artboards")[0]
            layers = d.read_gid_json(self.archive, gid_json)

        # if the file is Vectornator or older Curve
        else:
            # Does not work yet
            raise ValueError(f"Unsupported version: {version}. Version 5.0.0 or up is required.")

        return self

    def _check_if_curve(input_version: str):
        """check if the file version is 5.x or not"""
        required_version = version.parse("5.18.0")
        try:
            current_version = version.parse(input_version)
        except version.InvalidVersion:
            logging.warning(f"Invalid version string: {input_version}")
            return False

        return current_version >= required_version
