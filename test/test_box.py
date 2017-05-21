from nex.dampf.dvi_document import DVIDocument
from nex import box, box_writer


def test_glue_flex():
    h_box = box.HBox(contents=[box.Glue(dimen=100, stretch=50, shrink=20),
                               box.Glue(dimen=10, stretch=350, shrink=21)],
                     set_glue=False)
    assert h_box.stretch == [50 + 350]
    assert h_box.shrink == [20 + 21]


def test_glue_flex_set():
    h_box = box.HBox(contents=[box.Glue(dimen=100, stretch=50, shrink=20),
                               box.Glue(dimen=10, stretch=350, shrink=21)],
                     set_glue=True)
    assert h_box.stretch == [0]
    assert h_box.shrink == [0]


def test_box_writer():
    doc = DVIDocument(magnification=1000)
    lay_list = [
        box.Rule(1, 1, 1),
        box.Glue(1, 2, 3),
        box.HBox([
            box.Glue(3, 2, 1),
            box.Rule(3, 3, 3),
        ]),
    ]
    box_writer.write_box_to_doc(doc, lay_list)
