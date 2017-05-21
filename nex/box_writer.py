import subprocess

from .dampf.dvi_document import DVIDocument
from .parameters import Parameters
from . import box


def write_box_to_doc(doc, layout_list, horizontal=False):
    for item in layout_list:
        if isinstance(item, box.FontDefinition):
            doc.define_font(item.font_nr, item.font_name,
                            font_path=item.file_name)
        elif isinstance(item, box.FontSelection):
            doc.select_font(item.font_nr)
        elif isinstance(item, box.HBox):
            doc.push()
            doc.down(-item.offset)
            write_box_to_doc(doc, item.contents, horizontal=True)
            doc.pop()
            if horizontal:
                doc.right(item.width)
            else:
                doc.down(item.height)
        elif isinstance(item, box.VBox):
            doc.push()
            doc.right(item.offset)
            write_box_to_doc(doc, item.contents, horizontal=False)
            doc.pop()
            if horizontal:
                doc.right(item.width)
            else:
                doc.down(item.height)
        elif isinstance(item, box.Character):
            doc.put_char(item.code)
            doc.right(item.width)
        elif isinstance(item, box.Glue) and not item.is_set:
            if not horizontal:
                item.set_naturally()
            amount = item.length
            if horizontal:
                doc.right(amount)
            else:
                doc.down(amount)
        elif (isinstance(item, box.Kern) or
              (isinstance(item, box.Glue) and item.is_set)):
            amount = item.length
            if horizontal:
                doc.right(amount)
            else:
                doc.down(amount)
        elif isinstance(item, box.Rule):
            doc.put_rule(item.height, item.width)
            if horizontal:
                doc.right(item.width)
            else:
                doc.down(item.height)
        else:
            import pdb; pdb.set_trace()


def write_to_dvi_file(state, out_stream, write_pdf=False):
    magnification = state.parameters.get(Parameters.mag)
    doc = DVIDocument(magnification)
    total_layout_list = state.finish_up()
    write_box_to_doc(doc, total_layout_list)
    doc.write(out_stream)
    if write_pdf:
        if not isinstance(out_stream, str):
            raise ValueError('Cannot convert non-file-name to PDF')
        subprocess.run(['dvipdf', out_stream], check=True)
