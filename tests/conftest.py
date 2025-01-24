import random

import pytest


@pytest.fixture()
def max_length():

    return random.randint(500, 5000)
