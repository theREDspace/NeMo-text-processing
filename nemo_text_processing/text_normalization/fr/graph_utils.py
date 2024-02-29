# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
# Copyright 2015 and onwards Google, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.fr.utils import get_abs_path
from nemo_text_processing.text_normalization.fr.utils import load_labels


def roman_to_int(fst: 'pynini.FstLike') -> 'pynini.FstLike':
    """
    Alters given fst to convert Roman integers (lower and upper cased) into Arabic numerals. Valid for values up to 1000.
    e.g.
        "V" -> "5"
        "i" -> "1"

    Args:
        fst: Any fst. Composes fst onto Roman conversion outputs.
    """

    def _load_roman(file: str):
        roman = load_labels(get_abs_path(file))
        roman_numerals = [(x, y) for x, y in roman] + [(x.upper(), y) for x, y in roman]
        return pynini.string_map(roman_numerals)

    digit = _load_roman("data/roman/digit.tsv")
    ties = _load_roman("data/roman/ties.tsv")
    hundreds = _load_roman("data/roman/hundreds.tsv")
    thousands = _load_roman("data/roman/thousands.tsv")

    graph = (
        digit
        | ties + (digit | pynutil.add_weight(pynutil.insert("0"), 0.01))
        | (
            hundreds
            + (ties | pynutil.add_weight(pynutil.insert("0"), 0.01))
            + (digit | pynutil.add_weight(pynutil.insert("0"), 0.01))
        )
        | (
            thousands
            + (hundreds | pynutil.add_weight(pynutil.insert("0"), 0.01))
            + (ties | pynutil.add_weight(pynutil.insert("0"), 0.01))
            + (digit | pynutil.add_weight(pynutil.insert("0"), 0.01))
        )
    ).optimize()
    return graph @ fst