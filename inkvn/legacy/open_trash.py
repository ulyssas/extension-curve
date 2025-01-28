"""
Vectornator Inspection (2024/12/7)

description: Linearity Curve file reader(5.18.x) with tons of AI code

usage: python open_vectornator.py file.curve

what works (2025/01/09): limited SVG export (no text, other units)
"""

import logging
import traceback
import zipfile

import inkex
from packaging import version

# Vectornator Inspection
import decoders as d
import extract as ext


def open(stream):
    """
    Open and convert Linearity Curve (.curve) files.

    Vectornator (.vectornator) file is not supported.

    You can upgrade file format by opening vectornator file in Linearity Curve, then export as .curve.
    """
    try:
        with zipfile.ZipFile(stream, 'r') as archive:
            # Extract Manifest.json
            manifest = ext.extract_manifest(archive)

            # Extract Document.json
            document = ext.extract_document(archive, manifest)

            # Extract Drawing Data
            drawing_data = ext.extract_drawing_data(document)

            # Process Units and Artboards
            units = drawing_data["settings"]["units"]
            version = document["appVersion"]
            file_version = manifest["fileFormatVersion"]
            artboard_paths = drawing_data["artboardPaths"]

            # will be used later (as Inkscape attribute)
            print(f"Unit: {units}")

            assert len(artboard_paths), "No artboard paths found in the document."



            for abd in artboard_paths:
                with inner_zip.open(abd) as abdf:
                    artboard = json.load(abdf)
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















            # Read Artboard (GUID JSON)
            # If there's multiple artboards, only the first will be parsed.
            # TODO support for multiple artboards
            gid_json = ext.extract_gid_json(archive, artboard_paths[0])

            # if the file is Linearity Curve
            if check_if_curve(version):
                print(f"Supported version: {version}.")
                artboard = gid_json["artboards"][0]

                # main work here
                layers = d.read_gid_json(archive, gid_json)
                return layers

            # if the file is Vectornator
            else:
                # Does not work yet
                raise ValueError(
                    f"Unsupported version: {version}. Version 5.0.0 or up is required.")


    except zipfile.BadZipFile:
        logging.error("The provided file is not a valid ZIP archive.")
    except KeyError as e:
        logging.error(f"Required file missing in the archive: {e}")
    except ValueError as e:
        logging.error(
            f"An error occurred while reading file. {traceback.format_exc()}")
    except NotImplementedError as e:
        logging.error(f"File contains unsupported feature. {e}")
    except Exception as e:
        logging.error(
            f"An unexpected error occurred: {traceback.format_exc()}")


def check_if_curve(input_version: str) -> bool:
    """check if the file version is 5.x or not"""
    required_version = version.parse("5.0.0")
    current_version = version.parse(input_version)

    if current_version < required_version:
        return False
    else:
        return True
