import os
import sys

import pytest
from moto import mock_aws

from test_utils.mock_resources import setup_resources

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../lambda/dataPortal/"))
)


@pytest.fixture(autouse=True, scope="session")
def resources_dict():
    with mock_aws():
        yield setup_resources()
