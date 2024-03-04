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
import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.en.graph_utils import GraphFst, delete_space, insert_space, NEMO_NOT_QUOTE, NEMO_SIGMA

class TimeFst(GraphFst):
    """
    Finite state transducer for verbalizing time, e.g.
        time { hours: "onze" minutes: "quarante-cinq" } -> onze heures et trois quarts
        time { hours: "douze" minutes: "trente" } -> midi et demi
        time { hours: "douze" } -> midi

    Args:
        deterministic: if True will provide a single transduction option,
            for False multiple transduction are generated (used for audio-based normalization)
    """

    def __init__(self, deterministic: bool = True):
        super().__init__(name="time", kind="verbalize", deterministic=deterministic)
        
        hour = (
            pynutil.delete("hours:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )
        minute = (
            pynutil.delete("minutes:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )
        second = (
            pynutil.delete("seconds:")
            + delete_space
            + pynutil.delete("\"")
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete("\"")
        )
        special_cases = pynini.cdrewrite(
            pynini.cross("douze heures", "midi")
            | pynini.cross("zéro heures", "minuit")
            | pynini.cross("une minutes", "une minute")
            | pynini.cross("une secondes", "une seconde")
            | pynini.cross("une heures", "une heure"),
            pynini.union(" ", "[BOS]"),
            "",
            NEMO_SIGMA,
        )
        minute_special_cases = minute @ pynini.cdrewrite(
            pynini.cross("quinze", "et quart")
            | pynini.cross("trente", "et demie")
            | pynini.cross("quarante-cinq", "et trois quarts"), 
            pynini.union(" ", "[BOS]"),
            "[EOS]", 
            NEMO_SIGMA
        )

        graph_h = (
            hour
            + pynutil.insert(" heures")
            + delete_space
        )
        graph_h @= special_cases
        
        graph_hm = (
            hour
            + pynutil.insert(" heures ")
            + delete_space
            + minute_special_cases
        )
        graph_hm @= special_cases

        graph_hms = (
            hour
            + pynutil.insert(" heures ")
            + delete_space
            + minute
            + pynutil.insert(" minutes ")
            + delete_space
            + pynutil.insert(" et ")
            + second
            + pynutil.insert(" secondes")
        )

        graph_hms @= special_cases

        graph = graph_h
        graph |= graph_hm
        graph |= graph_hms
        self.graph = graph

        # Clean up and optimize the FST
        self.fst = self.delete_tokens(self.graph).optimize()