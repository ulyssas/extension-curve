# This file contains codes from:
# https://github.com/avibrazil/NSKeyedUnArchiver (LGPL3)
# https://gitlab.com/inkscape/extras/extension-afdesign (GPL2+)
# https://github.com/mohanson/leb128 (MIT)

import copy
import datetime
import plistlib
from dataclasses import fields
from io import BytesIO
from typing import Dict, List, Tuple

from lxml import etree


# from extension-afdesign
def to_pretty_xml(xml_string: bytes) -> bytes:
    """Return a pretty xml string with newlines and indentation."""
    # from https://stackoverflow.com/a/3974112/1320237
    # and https://stackoverflow.com/a/9612463/1320237
    parser = etree.XMLParser(remove_blank_text=True)
    file = BytesIO()
    file.write(xml_string)
    file.seek(0)
    element = etree.parse(file, parser)
    return etree.tostring(element, pretty_print=True)


def asdict_shallow(obj) -> Dict:
    """Convert dataclasses into dict, but only the to-level."""
    return {f.name: getattr(obj, f.name) for f in fields(obj)}


# from leb128
def _decode_leb128(b: bytearray) -> int:
    """Decode the unsigned leb128 encoded bytearray."""
    r = 0
    for i, e in enumerate(b):
        r = r + ((e & 0x7F) << (i * 7))
    return r


def read_varint(r: bytes, offset: int) -> Tuple[int, int]:
    """
    Decode the unsigned leb128 encoded value and returns (value, updated offset).
    """
    a = bytearray()
    while True:
        b = r[offset]
        offset += 1
        a.append(b)

        # continue decode if MSB is 1
        if (b & 0x80) == 0:
            break
    return _decode_leb128(a), offset


# from NSKeyedUnArchiver
def _unserialize(
    o: dict, serialized: dict, removeClassName: bool, plist_top: bool = True
):
    if plist_top:
        reassembled = copy.deepcopy(o)
    else:
        reassembled = o

    finished = False
    while not finished:
        finished = True

        cursor = None
        if isinstance(reassembled, bytes):
            try:
                return NSKeyedUnarchiver(reassembled)
            except:
                # Not plist data, just plain binary
                return reassembled
        elif isinstance(reassembled, dict):
            cursor = reassembled.keys()
        elif isinstance(reassembled, list):
            cursor = range(len(reassembled))
        else:  # str, int etc
            print("reassembled is a " + str(type(reassembled)) + ":" + str(reassembled))
            return reassembled

        for k in cursor:
            #  print(f"cursor={k}")
            # UIDs references items in "serialized" ($objects)
            if isinstance(reassembled[k], plistlib.UID):
                reassembled[k] = copy.deepcopy(serialized[reassembled[k].data])

                # $null gets replaced by None
                if str(reassembled[k]) == "$null":
                    reassembled[k] = None

                finished = False

            elif isinstance(reassembled[k], dict) or isinstance(reassembled[k], list):
                reassembled[k] = _unserialize(
                    reassembled[k], serialized, removeClassName, plist_top=False
                )

                if (
                    "$class" in reassembled[k]
                    and "$classes" in reassembled[k]["$class"]
                ):
                    # Specialized handler for common class types
                    if "NSArray" in reassembled[k]["$class"]["$classes"]:
                        reassembled[k] = reassembled[k]["NS.objects"]

                    elif any(
                        c in reassembled[k]["$class"]["$classes"]
                        for c in ["NSMutableDictionary", "NSDictionary"]
                    ):
                        reassembled[k] = dict(
                            zip(reassembled[k]["NS.keys"], reassembled[k]["NS.objects"])
                        )

                    elif any(
                        c in reassembled[k]["$class"]["$classes"]
                        for c in ["NSMutableString", "NSString"]
                    ):
                        reassembled[k] = reassembled[k]["NS.string"]

                    elif any(
                        c in reassembled[k]["$class"]["$classes"]
                        for c in ["NSMutableData", "NSData"]
                    ):
                        reassembled[k] = reassembled[k]["NS.data"]

                    elif "NSDate" in reassembled[k]["$class"]["$classes"]:
                        apple2001reference = datetime.datetime(
                            2001, 1, 1, tzinfo=datetime.timezone.utc
                        )
                        reassembled[k] = datetime.datetime.fromtimestamp(
                            reassembled[k]["NS.time"] + apple2001reference.timestamp(),
                            datetime.timezone.utc,
                        )
                    if removeClassName and isinstance(reassembled[k], dict):
                        # Remove visual polution
                        if "$class" in reassembled[k]:  # check if it's there
                            del reassembled[k]["$class"]

                finished = True
            else:
                # strings will remain unchanged.
                pass

    return reassembled


def _decode_attrib_info(data: bytes) -> List[Dict]:
    """
    decodes NSAttributeInfo in KeyedArchived NSAttributedString.
    """
    offset = 0
    runs = []

    while offset < len(data):
        try:
            length, offset = read_varint(data, offset)
            attr_id, offset = read_varint(data, offset)

            runs.append({"length": length, "attribute_id": attr_id})
        except IndexError:
            break
    return runs


def NSKeyedUnarchiver(plist, removeClassName=True):
    """
    plist can be:
    • bytes      ⟹ pass it through plistlib.loads()
    • dict       ⟹ unserialize
    """
    # removed other formats as they are not needed

    if isinstance(plist, bytes):
        plistdata = plistlib.loads(plist)
    elif isinstance(plist, dict):
        # plist is already a plistlib-parsed dict
        plistdata = plist
    else:
        raise TypeError(
            "Trying to plist-parse something that is neither a PurePath, file name, XML text, plist bytes stream nor a dict."
        )

    if "$top" in plistdata:
        o = copy.deepcopy(plistdata["$top"])
        unserialized = _unserialize(o, plistdata["$objects"], removeClassName)
    else:
        raise TypeError("Passed object is not an NSKeyedArchiver")

    if len(unserialized) == 1 and "root" in unserialized:
        # Unserialized data contains only 1 object, so no need to nest it under 'root'
        unserialized = unserialized["root"]

    if unserialized.get("NSAttributeInfo") is not None:
        attr_info = unserialized["NSAttributeInfo"]
        attr_bytes = attr_info if isinstance(attr_info, bytes) else bytes(attr_info)
        unserialized["NSAttributeInfo"] = _decode_attrib_info(attr_bytes)

    return unserialized
