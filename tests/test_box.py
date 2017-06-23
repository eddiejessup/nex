from nex.dampf.dvi_document import DVIDocument
from nex import box, box_writer


def test_glue_flex():
    h_box = box.HBox(contents=[box.Glue(dimen=100, stretch=50, shrink=20),
                               box.Glue(dimen=10, stretch=350, shrink=21),
                               box.Kern(dimen=100)],
                     set_glue=False)
    assert h_box.stretch == [50 + 350]
    assert h_box.shrink == [20 + 21]
    assert h_box.natural_length == 100 + 10 + 100


def test_kern():
    kern = box.Kern(dimen=100)
    assert kern.length == 100


def test_glue_flex_set():
    h_box = box.HBox(contents=[box.Glue(dimen=100, stretch=50, shrink=20),
                               box.Glue(dimen=10, stretch=350, shrink=21)],
                     set_glue=True)
    assert h_box.stretch == [0]
    assert h_box.shrink == [0]


def test_box_writer():
    doc = DVIDocument(magnification=1000)
    v_box = box.VBox([
        box.Rule(1, 1, 1),
        box.Glue(1, 2, 3),
        box.HBox([
            box.Glue(3, 2, 1),
            box.Rule(3, 3, 3),
        ]),
    ])
    box_writer.write_box_to_doc(doc, v_box)
