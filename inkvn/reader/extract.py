"""
VI extractors

reads Vectornator / Linearity Curve JSON data from .vectornator or .curve files.
"""


import base64
import json
import logging
import zipfile
from typing import Any, Dict


def read_json_from_zip(archive: zipfile.ZipFile, file_name: str) -> Dict[str, Any]:
    """Reads JSON file from zip, handling nested folders."""
    try:
        # Check if the file exists at the top level
        if file_name in archive.namelist():
            with archive.open(file_name) as f:
                return json.load(f)

        # Search for the file within nested folders if not found at the top level
        for name in archive.namelist():
            if name.endswith(file_name):
                with archive.open(name) as f:
                    return json.load(f)

        # Raise an error if the file is not found anywhere in the archive
        raise FileNotFoundError(f"File '{file_name}' not found in the zip archive.")

    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Failed to read or parse JSON file '{file_name}': {e}")
        raise  # Re-raise the exception after logging.


def read_dat_from_zip(archive: zipfile.ZipFile, file_name: str) -> str:
    """Encode dat (bitmap) file from zip (Vectornator file) in Base64 string."""
    try:
        if file_name in archive.namelist():
            with archive.open(file_name) as f:
                return base64.b64encode(f.read()).decode('utf-8')

        for name in archive.namelist():
            if name.endswith(file_name):
                with archive.open(name) as f:
                    return base64.b64encode(f.read()).decode('utf-8')

        raise FileNotFoundError(f"File '{file_name}' not found in the zip archive.")

    except Exception as e:
        logging.error(f"Failed to read or encode bitmap file '{file_name}': {e}")
        raise


def extract_manifest(archive: zipfile.ZipFile) -> Dict[str, Any]:
    """Extract and parse the Manifest.json."""
    return read_json_from_zip(archive, "Manifest.json")


def extract_document(archive: zipfile.ZipFile, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and parse the Document.json specified in the Manifest."""
    document_name = manifest.get("documentJSONFilename", "Document.json")
    return read_json_from_zip(archive, document_name)


def extract_drawing_data(document: Dict[str, Any]) -> Dict[str, Any]:
    """Return the 'drawing' data from the Document.json."""
    return document.get("drawing")


def extract_gid_json(archive: zipfile.ZipFile, artboard_path: str) -> Dict[str, Any]:
    """Extract and parse a GUID JSON file (artboard)."""
    return read_json_from_zip(archive, artboard_path)
