import pytest
from jira import JIRAError
from requests.exceptions import ConnectionError, RequestException

from planning_poker_jira.utils import get_error_text


@pytest.mark.parametrize('error, context, expected_result', [
    (JIRAError(400, 'foo'), {}, 'foo'),
    (JIRAError(401), {}, 'Could not authenticate the API user with the given credentials. '
                         'Make sure that you entered the correct data.'),
    (JIRAError(404), {}, 'The story does probably not exist inside the selected backend.'),
    (JIRAError(404), {'connection': 'test-connection'}, 'The story does probably not exist inside "test-connection".'),
    (JIRAError(1337), {}, 'Received status code 1337.'),
    (ConnectionError(), {}, 'Failed to connect to server.'),
    (ConnectionError(), {'api_url': 'https://foo.bar'}, 'Failed to connect to server. '
                                                        'Is "https://foo.bar" the correct API URL?'),
    (RequestException(), {}, 'There was an ambiguous error with your request. Check if all your data is correct.'),
    (Exception(), {}, 'Encountered an unknown exception.'),
])
def test_get_error_text(error, context, expected_result):
    assert get_error_text(error, **context) == expected_result
