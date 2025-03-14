# Copyright (C) 2024 Jonathan Neuhauser <jonathan.neuhauser@outlook.com>
# SPDX-License-Identifier: GPL-2.0-or-later

from inkvn.vninput import CurveInput
from inkex.tester import ComparisonMixin, TestCase
from inkex.tester.filters import CompareOrderIndependentStyle


class TestCurveConverter(ComparisonMixin, TestCase):
    """Run-through tests of CurveConverter"""

    effect_class = CurveInput
    compare_file = [
        "./artboards_and_guides.curve",
        "./blend_modes.curve",
        "./blur.curve",
        "./gradient.curve",
        "./image.curve",
        "./text.curve",
        "./variousshapes.curve",
        "./artboards_and_guides.vectornator",
        "./blend_modes.vectornator",
        "./blur.vectornator",
        "./gradient.vectornator",
        "./image.vectornator",
        "./text.vectornator",
        "./variousshapes.vectornator"
    ]

    comparisons = [tuple()]
    compare_filters = [CompareOrderIndependentStyle()]

