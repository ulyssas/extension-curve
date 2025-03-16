import io
import json
import zipfile

import pytest

from inkvn.reader.extract import read_json_from_zip


@pytest.fixture
def simple_zip_with_json():
    """zip file with dummy JSON data."""
    json_data = {"key": "value"}

    # create zip file on memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("test.json", json.dumps(json_data))

    zip_buffer.seek(0)
    return zip_buffer


@pytest.fixture
def nested_zip_with_json():
    """zip file with another zip file containing dummy JSON data."""
    json_data = {"nested": "data"}

    # create zip file
    nested_zip_buffer = io.BytesIO()
    with zipfile.ZipFile(nested_zip_buffer, "w") as nested_zip:
        nested_zip.writestr("nested.json", json.dumps(json_data))

    # include the zip in another zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("inner.curve", nested_zip_buffer.getvalue())

    zip_buffer.seek(0)
    return zip_buffer


def test_read_json_from_simple_zip(simple_zip_with_json):
    """Test reading JSON from a simple zip file."""
    with zipfile.ZipFile(simple_zip_with_json, "r") as archive:
        data = read_json_from_zip(archive, "test.json")

    assert data == {"key": "value"}


def test_read_json_from_nested_zip(nested_zip_with_json):
    """Test reading JSON from a nested zip file."""
    with zipfile.ZipFile(nested_zip_with_json, "r") as archive:
        data = read_json_from_zip(archive, "nested.json")

    assert data == {"nested": "data"}
