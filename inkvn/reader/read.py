"""
inkvn Reader

Reads Linearity Curve / Vectornator files and convert them into intermediate data.
"""

import logging
import zipfile
from typing import List

from packaging import version

import inkvn.reader.extract as ext
from inkvn.reader.decode import CurveDecoder

from ..elements.artboard import VNArtboard

logger = logging.getLogger(__name__)


class CurveReader:
    """
    inkvn CurveReader

    A Linearity Curve / Vectornator file reader to convert Curve documents into dataclasses.
    """

    def __init__(self, stream, is_debug: bool):
        self.is_debug: bool = is_debug
        self.archive = zipfile.ZipFile(stream, "r")
        self.file_version: int = 44  # main support
        self.app_version: str
        self.units: str = "px"
        self.artboards: List[VNArtboard] = []

        self.read()

    def read(self):
        manifest = ext.extract_manifest(self.archive)
        document = ext.extract_document(self.archive, manifest)
        drawing_data = ext.extract_drawing_data(document)

        assert drawing_data, "This document has no drawing data."

        self.units = drawing_data["settings"]["units"]
        self.app_version = document["appVersion"]
        self.file_version = manifest["fileFormatVersion"]
        artboard_paths = drawing_data["artboardPaths"]

        # different file versions have incompatible structure.
        # reporting App version & File version greatly helps
        if self.is_debug:
            logging.basicConfig(level=logging.INFO)
            logger.info(
                f"App version: {self.app_version}, File format: {self.file_version}, File name: {self.archive.filename}"
            )

        assert len(artboard_paths), "No artboard paths found in the document."

        # Read Artboard (GUID JSON)
        for artboard_path in artboard_paths:
            try:
                gid_json = ext.extract_gid_json(self.archive, artboard_path)
                decoder = CurveDecoder(
                    archive=self.archive,
                    gid_json=gid_json,
                    is_curve=self.check_if_curve(self.app_version),
                    file_version=self.file_version,
                )
                self.artboards.append(decoder.artboard)
            except FileNotFoundError as e:
                logger.error(f"read.py: {e} skipped reading the artboard.")

    def convert_unit(self):
        """Convert document unit to SVG."""
        unit_map = {
            "Points": "pt",
            "Picas": "pc",
            "Inches": "in",
            "Millimeters": "mm",
            "Centimeters": "cm",
            "Pixels": "px",
        }
        return unit_map.get(self.units, "px")

    @staticmethod
    def check_if_curve(input_version: str):
        """check if the app version is 5.x or not"""
        required_version = version.parse("5.1.0")
        try:
            current_version = version.parse(input_version)
        except version.InvalidVersion:
            logger.error(f"Invalid version string: {input_version}")
            return False

        return current_version >= required_version
