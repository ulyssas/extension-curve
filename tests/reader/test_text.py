from inkvn.reader.text import decode_new_text, decode_old_text


ENCODED_NEW_TEXT = {
    "alignment": {
        "values": [{"upperBound": 28, "value": 2}]
    },
    "fillColor": {
        "values": [
            {"upperBound": 7, "value": {"hsba": {"alpha": 1, "brightness": 0.5725490196078431,
                                                 "hue": 0.5266203703703703, "saturation": 0.9863013698630138}}},
            {"upperBound": 8, "value": {"hsba": {"alpha": 1, "brightness": 0.43529411764705883,
                                                 "hue": 0.470679012345679, "saturation": 0.9729729729729729}}},
            {"upperBound": 23, "value": {"hsba": {"alpha": 1,
                                                  "brightness": 1, "hue": 0, "saturation": 0}}},
            {"upperBound": 24, "value": {"hsba": {"alpha": 1, "brightness": 0.43529411764705883,
                                                  "hue": 0.470679012345679, "saturation": 0.9729729729729729}}},
            {"upperBound": 28, "value": {"hsba": {"alpha": 1, "brightness": 0.5725490196078431,
                                                  "hue": 0.5266203703703703, "saturation": 0.9863013698630138}}}
        ]
    },
    "fontName": {"values": [{"upperBound": 28, "value": "Helvetica-BoldOblique"}]},
    "fontSize": {"values": [{"upperBound": 28, "value": 106.29886627197266}]},
    "kerning": {"values": [{"upperBound": 28, "value": 0}]},
    "lineHeight": {"values": [{"upperBound": 28, "value": {"multiple": {"_0": 1.2}}}]},
    "strikethrough": {"values": [{"upperBound": 28, "value": False}]},
    "string": "Testing\nextension\ncurve\nnow!",
    "underline": {"values": [{"upperBound": 28, "value": False}]}
}

ENCODED_OLD_TEXT = {
    "NSString": "Testing\nextension\ncurve\nnow!",
    "NSAttributeInfo": [
        {"length": 7, "attribute_id": 0},
        {"length": 1, "attribute_id": 1},
        {"length": 15, "attribute_id": 2},
        {"length": 1, "attribute_id": 1},
        {"length": 4, "attribute_id": 0}
    ],
    "NSAttributes": [
        {
            "NSColor": {
                "UIColorComponentCount": 4,
                "UIRed": 0.007843137718737125,
                "UIGreen": 0.48235294222831726,
                "UIBlue": 0.572549045085907,
                "UIAlpha": 1.0,
                "NSColorSpace": 2,
            },
            "NSParagraphStyle": {
                "NSTabStops": None,
                "NSTextBlocks": [],
                "NSAllowsTighteningForTruncation": 1,
                "NSTighteningFactorForTruncation": 0.05000000074505806,
                "NSTextLists": [],
                "NSWritingDirection": 1,
                "NSAlignment": 1
            },
            "NSFont": {
                "NSName": "Helvetica-BoldOblique",
                "NSSize": 106.29886627197266,
                "UIFontMaximumPointSizeAfterScaling": 0.0,
                "UIFontPointSizeForScaling": 0.0,
                "UIFontTraits": 3,
                "UIFontPointSize": 106.29886627197266,
                "UIFontTextStyleForScaling": None,
                "UIFontName": "Helvetica-BoldOblique",
                "UISystemFont": False
            }
        },
        {
            "NSColor": {
                "UIColorComponentCount": 4,
                "UIRed": 0.0117647061124444,
                "UIGreen": 0.43529412150382996,
                "UIBlue": 0.3607843220233917,
                "UIAlpha": 1.0,
                "NSColorSpace": 2,
            },
            "NSParagraphStyle": {
                "NSTabStops": None,
                "NSTextBlocks": [],
                "NSAllowsTighteningForTruncation": 1,
                "NSTighteningFactorForTruncation": 0.05000000074505806,
                "NSTextLists": [],
                "NSWritingDirection": 1,
                "NSAlignment": 1
            },
            "NSFont": {
                "NSName": "Helvetica-BoldOblique",
                "NSSize": 106.29886627197266,
                "UIFontMaximumPointSizeAfterScaling": 0.0,
                "UIFontPointSizeForScaling": 0.0,
                "UIFontTraits": 3,
                "UIFontPointSize": 106.29886627197266,
                "UIFontTextStyleForScaling": None,
                "UIFontName": "Helvetica-BoldOblique",
                "UISystemFont": False
            }
        },
        {
            "NSColor": {
                "UIColorComponentCount": 4,
                "UIRed": 1.0,
                "UIGreen": 1.0,
                "UIBlue": 1.0,
                "UIAlpha": 1.0,
                "NSColorSpace": 2
            },
            "NSParagraphStyle": {
                "NSTabStops": None,
                "NSTextBlocks": [],
                "NSAllowsTighteningForTruncation": 1,
                "NSTighteningFactorForTruncation": 0.05000000074505806,
                "NSTextLists": [],
                "NSWritingDirection": 1,
                "NSAlignment": 1
            },
            "NSFont": {
                "NSName": "Helvetica-BoldOblique",
                "NSSize": 106.29886627197266,
                "UIFontMaximumPointSizeAfterScaling": 0.0,
                "UIFontPointSizeForScaling": 0.0,
                "UIFontTraits": 3,
                "UIFontPointSize": 106.29886627197266,
                "UIFontTextStyleForScaling": None,
                "UIFontName": "Helvetica-BoldOblique",
                "UISystemFont": False
            }
        }
    ]
}

DECODED_NEW_TEXT = [
    {
        "fillColor": {"hsba": {"alpha": 1, "brightness": 0.5725490196078431, "hue": 0.5266203703703703, "saturation": 0.9863013698630138}},
        "length": 7,
        "alignment": 2,
        "fontName": "Helvetica-BoldOblique",
        "fontSize": 106.29886627197266,
        "kerning": 0,
        "lineHeight": {"multiple": {"_0": 1.2}},
        "strikethrough": False,
        "underline": False
    },
    {
        "fillColor": {"hsba": {"alpha": 1, "brightness": 0.43529411764705883, "hue": 0.470679012345679, "saturation": 0.9729729729729729}},
        "length": 1,
        "alignment": 2,
        "fontName": "Helvetica-BoldOblique",
        "fontSize": 106.29886627197266,
        "kerning": 0,
        "lineHeight": {"multiple": {"_0": 1.2}},
        "strikethrough": False,
        "underline": False
    },
    {
        "fillColor": {"hsba": {"alpha": 1, "brightness": 1, "hue": 0, "saturation": 0}},
        "length": 15,
        "alignment": 2,
        "fontName": "Helvetica-BoldOblique",
        "fontSize": 106.29886627197266,
        "kerning": 0,
        "lineHeight": {"multiple": {"_0": 1.2}},
        "strikethrough": False,
        "underline": False
    },
    {
        "fillColor": {"hsba": {"alpha": 1, "brightness": 0.43529411764705883, "hue": 0.470679012345679, "saturation": 0.9729729729729729}},
        "length": 1,
        "alignment": 2,
        "fontName": "Helvetica-BoldOblique",
        "fontSize": 106.29886627197266,
        "kerning": 0,
        "lineHeight": {"multiple": {"_0": 1.2}},
        "strikethrough": False,
        "underline": False
    },
    {
        "alignment": 2,
        "length": 4,
        "fillColor": {"hsba": {"alpha": 1, "brightness": 0.5725490196078431, "hue": 0.5266203703703703, "saturation": 0.9863013698630138}},
        "fontName": "Helvetica-BoldOblique",
        "fontSize": 106.29886627197266,
        "kerning": 0,
        "lineHeight": {"multiple": {"_0": 1.2}},
        "strikethrough": False,
        "underline": False
    }
]

DECODED_OLD_TEXT = [
    {
        "alignment": 2,
        "length": 7,
        "fillColor": {"rgba": {"red": 0.007843137718737125, "green": 0.48235294222831726, "blue": 0.572549045085907, "alpha": 1.0}},
        "fontName": "Helvetica-BoldOblique",
        "fontSize": 106.29886627197266,
        "kerning": 0,
        "lineHeight": None,
        "strikethrough": False,
        "underline": False
    },
    {
        "alignment": 2,
        "length": 1,
        "fillColor": {"rgba": {"red": 0.0117647061124444, "green": 0.43529412150382996, "blue": 0.3607843220233917, "alpha": 1.0}},
        "fontName": "Helvetica-BoldOblique",
        "fontSize": 106.29886627197266,
        "kerning": 0,
        "lineHeight": None,
        "strikethrough": False,
        "underline": False
    },
    {
        "alignment": 2,
        "length": 15,
        "fillColor": {"rgba": {"red": 1.0, "green": 1.0, "blue": 1.0, "alpha": 1.0}},
        "fontName": "Helvetica-BoldOblique",
        "fontSize": 106.29886627197266,
        "kerning": 0,
        "lineHeight": None,
        "strikethrough": False,
        "underline": False
    },
    {
        "alignment": 2,
        "length": 1,
        "fillColor": {"rgba": {"red": 0.0117647061124444, "green": 0.43529412150382996, "blue": 0.3607843220233917, "alpha": 1.0}},
        "fontName": "Helvetica-BoldOblique",
        "fontSize": 106.29886627197266,
        "kerning": 0,
        "lineHeight": None,
        "strikethrough": False,
        "underline": False
    },
    {
        "alignment": 2,
        "length": 4,
        "fillColor": {"rgba": {"red": 0.007843137718737125, "green": 0.48235294222831726, "blue": 0.572549045085907, "alpha": 1.0}},
        "fontName": "Helvetica-BoldOblique",
        "fontSize": 106.29886627197266,
        "kerning": 0,
        "lineHeight": None,
        "strikethrough": False,
        "underline": False
    }
]


def test_decode_new_text():
    """Test new text format."""
    data = decode_new_text(ENCODED_NEW_TEXT)

    assert data == DECODED_NEW_TEXT


def test_decode_old_text():
    """Test legacy text format."""
    data = decode_old_text(ENCODED_OLD_TEXT)

    assert data == DECODED_OLD_TEXT
