from nex import box


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
