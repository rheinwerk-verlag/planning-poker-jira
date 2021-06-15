from requests.exceptions import ConnectionError, RequestException
from unittest.mock import Mock, patch, call

from django.contrib import messages
from jira import JIRAError
import pytest

from planning_poker_jira.admin import export_stories
from planning_poker_jira.forms import ExportStoriesForm


def test_initial_export_stories(jira_connection_admin, stories, rf, admin_user):
    request = rf.post('/')
    request.user = admin_user
    response = export_stories(jira_connection_admin, request, stories)
    assert type(response.context_data['form'].form) == ExportStoriesForm
    assert response.context_data['stories'] == stories


@pytest.mark.parametrize('side_effect, expected_message_user_calls', (
    (Mock(), (('2 stories were successfully exported.', messages.SUCCESS),)),
    (JIRAError(status_code=404), (
        ('"FIAE-1: Write tests" could not be exported. '
         'The story does probably not exist inside "http://test_url".', messages.ERROR),
        ('"FIAE-2: Write more tests" could not be exported. '
         'The story does probably not exist inside "http://test_url".', messages.ERROR),
    )),
    (ConnectionError, (
        ('"FIAE-1: Write tests" could not be exported. '
         'Failed to connect to server. Is "http://test_url" the correct API URL?', messages.ERROR),
        ('"FIAE-2: Write more tests" could not be exported. '
         'Failed to connect to server. Is "http://test_url" the correct API URL?', messages.ERROR),
    )),
    (RequestException, (
        ('"FIAE-1: Write tests" could not be exported. '
         'There was an ambiguous error with your request. Check if all your data is correct.', messages.ERROR),
        ('"FIAE-2: Write more tests" could not be exported. '
         'There was an ambiguous error with your request. Check if all your data is correct.', messages.ERROR),
    )),
))
@patch('planning_poker_jira.models.JiraConnection.get_client')
def test_confirmed_export_stories(mock_get_client, rf, admin_user, jira_connection_admin, stories,
                                  export_stories_form_data, side_effect, expected_message_user_calls):
    mock_client = Mock()
    mock_client.issue = Mock(side_effect=side_effect)
    mock_get_client.return_value = mock_client
    mock_message_user = Mock()

    request = rf.post('/', dict(**export_stories_form_data, export=True))
    request.user = admin_user
    with patch.object(jira_connection_admin, 'message_user', mock_message_user):
        response = export_stories(jira_connection_admin, request, stories)
    mock_message_user.assert_has_calls((call(request, *expected_call) for expected_call in expected_message_user_calls))
