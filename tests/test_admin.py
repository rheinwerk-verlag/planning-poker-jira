from unittest.mock import Mock, patch, call

import pytest
from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from jira import JIRAError
from requests.exceptions import ConnectionError, RequestException

from planning_poker.models import Story

from planning_poker_jira.admin import export_stories
from planning_poker_jira.forms import ExportStoriesForm, ImportStoriesForm


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


def test_import_stories_view_get(admin_client, jira_connection, jira_connection_admin):
    response = admin_client.get(reverse(admin_urlname(jira_connection_admin.opts, 'import_stories'),
                                        args=[jira_connection.id]))
    assert type(response.context_data['form'].form) == ImportStoriesForm


@pytest.mark.parametrize('side_effect, expected_errors, expected_message', (
    # The side effect has to be a list inside a list because `side_effect` will return the next element whenever it is
    # an iterable.
    ([[Story(ticket_number='FIAE-1', title='Write tests', description='Write some tests.')]], None,
     ('1 story was successfully imported.', messages.SUCCESS)),
    (JIRAError(status_code=1337), {'jql_query': ['Received status code 1337.']}, None),
    (ConnectionError, {'__all__': ['Failed to connect to server. Is "http://test_url" the correct API URL?']}, None),
    (RequestException, {
            '__all__': ['There was an ambiguous error with your request. Check if all your data is correct.']
        }, None)
))
@patch('planning_poker_jira.admin.JiraConnectionAdmin.message_user')
@patch('planning_poker_jira.models.JiraConnection.get_client')
@patch('planning_poker_jira.models.JiraConnection.create_stories')
def test_import_stories_view_post(mock_create_stories, mock_get_client, mock_message_user, admin_client, jira_connection,
                                  jira_connection_admin, side_effect, expected_errors, expected_message):

    mock_create_stories.side_effect = side_effect
    response = admin_client.post(reverse(admin_urlname(jira_connection_admin.opts, 'import_stories'),
                                         args=[jira_connection.id]), {'jql_query': 'key in "FIAE-1"',
                                                                      'poker_session': ''})
    if expected_errors:
        assert response.context_data['form'].form.errors == expected_errors
    if expected_message:
        mock_message_user.assert_called_with(response.wsgi_request, *expected_message)
