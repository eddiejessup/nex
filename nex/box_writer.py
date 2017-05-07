from nex.dampf.dvi_document import DVIDocument

from .tex_parameters import Parameters
from .box import (HBox, UnSetGlue, SetGlue, Character, FontDefinition,
                  FontSelection)


def write_box_to_doc(doc, layout_list, horizontal=False):
    for item in layout_list:
        if isinstance(item, FontDefinition):
            doc.define_font(item.font_nr, item.font_name,
                            font_path=item.file_name)
        elif isinstance(item, FontSelection):
            doc.select_font(item.font_nr)
        elif isinstance(item, HBox):
            doc.push()
            write_box_to_doc(doc, item.contents, horizontal=True)
            doc.pop()
            if horizontal:
                doc.right(item.width)
        elif isinstance(item, Character):
            doc.set_char(item.code)
        elif isinstance(item, UnSetGlue):
            if not horizontal:
                item = item.set(item.natural_dimen)
            amount = item.dimen
            if horizontal:
                # doc.put_rule(height=1000, width=amount)
                doc.right(amount)
            else:
                doc.down(amount)
        elif isinstance(item, SetGlue):
            amount = item.dimen
            if horizontal:
                # doc.put_rule(height=1000, width=amount)
                doc.right(amount)
            else:
                doc.down(amount)
        else:
            import pdb; pdb.set_trace()


def write_to_file(state, out_path):
    magnification = state.parameters.get_parameter_value(Parameters.mag)
    doc = DVIDocument(magnification)
    total_layout_list = state.pop_mode()
    write_box_to_doc(doc, total_layout_list)
    doc.write(out_path)
