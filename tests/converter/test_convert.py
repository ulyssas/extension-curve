# Copyright (C) 2024 Jonathan Neuhauser <jonathan.neuhauser@outlook.com>
# SPDX-License-Identifier: GPL-2.0-or-later

from inkex.tester import ComparisonMixin, TestCase
from inkex.tester.filters import CompareOrderIndependentStyle

from inkvn.vninput import CurveInput


class TestCurveConverter(ComparisonMixin, TestCase):
    """Run-through tests of CurveConverter"""

    effect_class = CurveInput
    compare_file = [
        "./artboards_and_guides_44.curve",
        "./artboards_and_guides_51.curve",
        "./blend_modes_44.curve",
        "./blend_modes_51.curve",
        "./blur_44.curve",
        "./blur_51.curve",
        "./brush_44.curve",
        "./brush_51.curve",
        "./gradient_44.curve",
        "./gradient_51.curve",
        "./image_40.curve",
        "./image_44.curve",
        "./image_51.curve",
        "./variousshapes_44.curve",
        "./variousshapes_51.curve",
        "./artboards_and_guides.vectornator",
        "./blend_modes.vectornator",
        "./blur.vectornator",
        "./brush.vectornator",
        "./gradient.vectornator",
        "./image.vectornator",
        "./variousshapes.vectornator",
    ]

    comparisons = [tuple()]
    compare_filters = [CompareOrderIndependentStyle()]


class TestCurveConverterWithErrorMessages(ComparisonMixin, TestCase):
    effect_class = CurveInput
    compare_file = [
        "./text_44.curve",
        "./text_51.curve",
        "./text.vectornator",
    ]

    comparisons = [tuple()]
    compare_filters = [CompareOrderIndependentStyle()]
    stderr_protect = False
