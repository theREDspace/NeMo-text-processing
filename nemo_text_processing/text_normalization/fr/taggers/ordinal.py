# Copyright (c) 2023, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
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


from nemo_text_processing.text_normalization.fr.graph_utils import roman_to_int
import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.en.graph_utils import NEMO_SPACE, GraphFst
from nemo_text_processing.text_normalization.fr.utils import get_abs_path

class OrdinalFst(GraphFst):
    """
    Finite state transducer for classifying ordinal
        	"2e" -> ordinal { integer: "deux" morphosyntactic_features: "ième" }
    This grammar covers from single digits to hundreds of billions ("milliardième" in French).
    This FST also records the ending of the ordinal (called "morphosyntactic_features").
    Args:
        cardinal: CardinalFst
        deterministic: if True will provide a single transduction option,
            for False multiple transduction are generated (used for audio-based normalization)
    """

    def __init__(self, cardinal: GraphFst, deterministic: bool = True):
        super().__init__(name="ordinal", kind="classify")

        numbers = cardinal.all_nums_no_tokens
        numbers_graph = pynutil.insert("integer: \"") + numbers + pynutil.insert("\"")

        suffixes = pynini.string_file(get_abs_path("data/ordinals/suffixes.tsv"))
        suffixes_graph = pynutil.insert("morphosyntactic_features: \"") + suffixes + pynutil.insert("\"")

        ordinal_graph = numbers_graph + pynutil.insert(NEMO_SPACE) + suffixes_graph
        self.graph = ordinal_graph

        romans = roman_to_int(numbers)
        exceptions = pynini.string_file(get_abs_path("data/ordinals/roman_exceptions.tsv"))
        graph_exception = pynini.project(exceptions, 'input')
        romans_ordinal = (pynini.project(romans, "input") - graph_exception.arcsort()) @ romans
        
        romans_graph = pynutil.insert("integer: \"") + romans_ordinal + pynutil.insert("\"")
        romans_ordinal_graph = romans_graph + pynutil.insert(NEMO_SPACE) + suffixes_graph
        
        self.graph = pynini.union(self.graph, romans_ordinal_graph).optimize()
        final_graph = self.add_tokens(self.graph)
        
        self.fst = final_graph.optimize()
