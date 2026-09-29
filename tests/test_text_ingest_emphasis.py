from cardsmith.ingest.text import _strip_emphasis_markers


def test_strips_single_underscore_emphasis_markers():
    assert _strip_emphasis_markers("The _mitochondrion_ is small.") == "The mitochondrion is small."


def test_leaves_unrelated_underscores_alone():
    assert _strip_emphasis_markers("a_variable_name stays") == "a_variable_name stays"
