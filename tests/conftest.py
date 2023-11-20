from fair import FairClient
import os
import pytest

FAIRCOMPUTE_SERVER_URL = os.environ.get('FAIRCOMPUTE_SERVER_URL', 'http://localhost:8000')
FAIRCOMPUTE_USER_EMAIL = os.environ.get('FAIRCOMPUTE_USER_EMAIL', 'debug-usr')
FAIRCOMPUTE_USER_PASSWORD = os.environ.get('FAIRCOMPUTE_USER_PASSWORD', 'debug-pwd')


@pytest.fixture
def fair_client():
    return FairClient(server_address=FAIRCOMPUTE_SERVER_URL, user_email=FAIRCOMPUTE_USER_EMAIL, user_password=FAIRCOMPUTE_USER_PASSWORD)
