import pytest
from html_fragmentize.msg_split import split_message


def test_can_run(max_length):

    fragments = split_message("source.html", max_length)

    for fragment in fragments:
        assert len(fragment) <= max_length
