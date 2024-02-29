
import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.en.utils import augment_labels_with_punct_at_end
from nemo_text_processing.text_normalization.en.graph_utils import NEMO_DIGIT, NEMO_SPACE, GraphFst, convert_space, insert_space, delete_space
from nemo_text_processing.text_normalization.fr.utils import get_abs_path, load_labels


class TimeFst(GraphFst):
    """
    Finite state transducer for classifying time, e.g.
        00 h -> time { hours: "zèro" }
        8h30 -> time { hours: "huit" minutes: "trente" }
        20h -> time { hours: "vingt" }
        2 h 30 -> time { hours: "deux" minutes: "trente" }
        02 h 30 -> time { hours: "deux" minutes: "trente" }
        2h -> time { hours: "deux" }
        02:00 -> time { hours: "deux" }
        2:00 -> time { hours: "deux" }
        10:00:05 -> time { hours: "dix" minutes: "zero" seconds: "five" }
    
    Args:
        cardinal: CardinalFst
        deterministic: if True will provide a single transduction option,
            for False multiple transduction are generated (used for audio-based normalization)
    """

    def __init__(self, cardinal: GraphFst, deterministic: bool = True):
        super().__init__(name="time", kind="classify", deterministic=deterministic)
      
        # only used for < 1000 thousand -> 0 weight
        cardinal = cardinal.all_nums_no_tokens

        labels_hour = [str(x) for x in range(0, 24)]
        labels_minute_single = [str(x) for x in range(1, 10)]
        labels_minute_double = [str(x) for x in range(10, 60)]

        required_h_marker = pynutil.delete("h") | pynutil.delete(":")
        optional_min_marker = pynini.closure(pynutil.delete("min") | pynutil.delete("m"), 0, 1)
        
        delete_leading_zero_to_double_digit = (
            pynini.closure(pynutil.delete("0") | (NEMO_DIGIT - "0"), 0, 1) + NEMO_DIGIT
        )

        graph_hour = (
            pynini.closure(NEMO_DIGIT, 1, 2)
            @ delete_leading_zero_to_double_digit 
            @ pynini.union(*labels_hour) @ cardinal
        )
        
        graph_minute_single = pynini.union(*labels_minute_single) @ cardinal
        graph_minute_double = pynini.union(*labels_minute_double) @ cardinal

        final_graph_hour = pynutil.insert("hours: \"") + graph_hour + pynutil.insert("\"")
        final_graph_minute = (
            pynutil.insert(" minutes: \"")
            + (pynini.cross("0", "") + graph_minute_single | graph_minute_double)
            + pynutil.insert("\"")
        )
        final_graph_second = (
            pynutil.insert(" seconds: \"")
            + (pynini.cross("0", "") + graph_minute_single | graph_minute_double)
            + pynutil.insert("\"")
        )
        
        graph_h = ( # 12h, 12 h
            final_graph_hour
            + delete_space
            + required_h_marker
        )

        # # 12h30 and 12 h 30, 02:30, 2:00
        graph_hm = (
            final_graph_hour
            + delete_space
            + required_h_marker
            + delete_space
            + final_graph_minute + delete_space + optional_min_marker
        )

        # # 10 h 30min 15 s ,
        graph_hms = (
            final_graph_hour
            + delete_space
            + required_h_marker
            + delete_space
            + final_graph_minute + delete_space + optional_min_marker
            + delete_space
            + final_graph_second
        )
 
        final_graph = graph_h | graph_hm | graph_hms
        self.graph = final_graph.optimize()
        final_graph = self.add_tokens(self.graph)
        self.fst = final_graph.optimize()