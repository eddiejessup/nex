from nex import box


def test_stretch():
    h_box = box.HBox(contents=[box.Glue(dimen=100, stretch=50, shrink=20),
                               box.Glue(dimen=10, stretch=350, shrink=21)])
    assert h_box.stretch == [50 + 350]
    assert h_box.shrink == [20 + 21]
