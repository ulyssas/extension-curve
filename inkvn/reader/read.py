"""
inkvn Reader

Reads Linearity Curve files and convert them into intermediate data.
"""


import logging
import zipfile
from typing import List

from packaging import version

import inkvn.reader.decode as d
import inkvn.reader.extract as ext
from inkvn.reader.datatypes import Artboard


class CurveReader:
    """
    inkvn CurveReader

    A Linearity Curve file reader to convert Curve documents into dataclasses.

    TODO: Implement format differences
    """
    def __init__(self, stream):
        self.archive = zipfile.ZipFile(stream, 'r')
        self.artboards: List[Artboard] = []

        self.read()

    def read(self):
        manifest = ext.extract_manifest(self.archive)
        document = ext.extract_document(self.archive, manifest)
        drawing_data = ext.extract_drawing_data(document)

        units = drawing_data["settings"]["units"]
        version = document["appVersion"]
        file_version = manifest["fileFormatVersion"]
        artboard_paths = drawing_data["artboardPaths"]

        assert len(artboard_paths), "No artboard paths found in the document."

        # will be used later (as Inkscape attribute)
        print(f"Unit: {units}")

        # Step 5: Read Artboard (GUID JSON)
        # If there's multiple artboards, only the first will be exported(FOR NOW).
        # TODO: Add multiple artboard support
        gid_json = ext.extract_gid_json(self.archive, artboard_paths[0])

        # if the file is Linearity Curve
        if self.check_if_curve(version):
            print(f"Supported version: {version}.")

            # TODO: loading function should be here
            #artboard = gid_json.get("artboards")[0]
            artboard = d.read_artboard(self.archive, gid_json) # will be like this
            self.artboards.append(artboard)

            # raise ValueError(f"{artboard}") # I don't know how to print with Inkscape
        # if the file is Vectornator or older Curve
        else:
            # Does not work yet
            raise ValueError(f"Unsupported version: {version}. Version 5.0.0 or up is required.")

    @staticmethod
    def check_if_curve(input_version: str):
        """check if the file version is 5.x or not"""
        required_version = version.parse("5.0.0")
        try:
            current_version = version.parse(input_version)
        except version.InvalidVersion:
            logging.warning(f"Invalid version string: {input_version}")
            return False

        return current_version >= required_version
