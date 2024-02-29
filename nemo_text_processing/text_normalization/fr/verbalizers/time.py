import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.en.graph_utils import GraphFst, delete_space, insert_space, NEMO_NOT_QUOTE, NEMO_SIGMA

class TimeFst(GraphFst):
    """
    Finite state transducer for verbalizing time, e.g.
        time { hours: "twelve" minutes: "thirty" suffix: "a m" zone: "e s t" } -> twelve thirty a m e s t
        time { hours: "twelve" } -> twelve o'clock

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