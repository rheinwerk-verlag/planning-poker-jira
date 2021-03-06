from unittest.mock import Mock, call, patch

import pytest
from django.contrib import messages
from django.contrib.admin.sites import site
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from jira import JIRAError
from requests.exceptions import ConnectionError, RequestException

from planning_poker.models import Story
from planning_poker_jira.admin import JiraConnectionAdmin, export_story_points
from planning_poker_jira.forms import ExportStoryPointsForm, ImportStoriesForm
from planning_poker_jira.models import JiraConnection


@pytest.fixture
def jira_connection_admin():
    return JiraConnectionAdmin(JiraConnection, site)


class TestExportStoriesAction:
    def test_initial_export_story_points(self, jira_connection_admin, stories, rf, admin_user):
        request = rf.post('/')
        request.user = admin_user
        response = export_story_points(jira_connection_admin, request, stories)
        assert isinstance(response.context_data['form'].form, ExportStoryPointsForm)
        assert response.context_data['stories'] == stories

    @pytest.mark.parametrize('side_effect, expected_message_user_calls', (
        (Mock(), (('2 stories were successfully exported.', messages.SUCCESS),)),
        (JIRAError(status_code=404), (
            ('"FIAE-1: Write tests" could not be exported. '
             'The story does probably not exist inside "http://test_url".', messages.ERROR),
            ('"FIAE-2: Write more tests" could not be exported. '
             'The story does probably not exist inside "http://test_url".', messages.ERROR),
        )),
        (ConnectionError(), (
            ('"FIAE-1: Write tests" could not be exported. '
             'Failed to connect to server. Is "http://test_url" the correct API URL?', messages.ERROR),
            ('"FIAE-2: Write more tests" could not be exported. '
             'Failed to connect to server. Is "http://test_url" the correct API URL?', messages.ERROR),
        )),
        (RequestException(), (
            ('"FIAE-1: Write tests" could not be exported. '
             'There was an ambiguous error with your request. Check if all your data is correct.', messages.ERROR),
            ('"FIAE-2: Write more tests" could not be exported. '
             'There was an ambiguous error with your request. Check if all your data is correct.', messages.ERROR),
        )),
    ))
    @patch('planning_poker_jira.models.JiraConnection.get_client')
    def test_confirmed_export_story_points(self, mock_get_client, rf, admin_user, jira_connection,
                                           jira_connection_admin, stories, side_effect, expected_message_user_calls):
        mock_client = Mock()
        mock_client.issue = Mock(side_effect=side_effect)
        mock_get_client.return_value = mock_client
        mock_message_user = Mock()

        request = rf.post('/', dict(**{'jira_connection': jira_connection.pk}, export=True))
        request.user = admin_user
        with patch.object(jira_connection_admin, 'message_user', mock_message_user):
            export_story_points(jira_connection_admin, request, stories)
        mock_message_user.assert_has_calls(
            (call(request, *expected_call) for expected_call in expected_message_user_calls)
        )
        if not isinstance(side_effect, Exception):
            side_effect().update.assert_has_calls(call(fields={'testfield': story.story_points}) for story in stories)


class TestJiraConnectionAdmin:
    def test_import_stories_view_get(self, admin_client, jira_connection, jira_connection_admin):
        response = admin_client.get(reverse(admin_urlname(jira_connection_admin.opts, 'import_stories'),
                                            args=[jira_connection.id]))
        assert isinstance(response.context_data['form'].form, ImportStoriesForm)

    @pytest.mark.parametrize('side_effect, expected_errors, expected_message', (
        # The side effect has to be a list inside a list because `side_effect` will return the next element whenever it
        # is an iterable.
        ([[Story(ticket_number='FIAE-1', title='Write tests', description='Write some tests.')]], None,
         ('1 story was successfully imported.', messages.SUCCESS)),
        (JIRAError(status_code=1337), {'jql_query': ['Received status code 1337.']}, None),
        (ConnectionError(), {'__all__': ['Failed to connect to server. Is "http://test_url" the correct API URL?']},
         None),
        (RequestException(), {
            '__all__': ['There was an ambiguous error with your request. Check if all your data is correct.']
        }, None)
    ))
    @patch('planning_poker_jira.admin.JiraConnectionAdmin.message_user')
    @patch('planning_poker_jira.models.JiraConnection.get_client')
    @patch('planning_poker_jira.models.JiraConnection.create_stories')
    def test_import_stories_view_post(self, mock_create_stories, mock_get_client, mock_message_user, admin_client,
                                      jira_connection, jira_connection_admin, side_effect, expected_errors,
                                      expected_message):

        mock_create_stories.side_effect = side_effect
        jql_query = 'key in "FIAE-1"'
        response = admin_client.post(reverse(admin_urlname(jira_connection_admin.opts, 'import_stories'),
                                             args=[jira_connection.id]), {'jql_query': jql_query,
                                                                          'poker_session': ''})
        mock_create_stories.assert_called_with(jql_query, None, mock_get_client())
        if expected_errors:
            assert response.context_data['form'].form.errors == expected_errors
        if expected_message:
            mock_message_user.assert_called_with(response.wsgi_request, *expected_message)

    def test_import_stories_view_no_object_found(self, admin_client, jira_connection_admin):
        response = admin_client.get(reverse(admin_urlname(jira_connection_admin.opts, 'import_stories'),
                                            args=[9001]))
        assert response.status_code == 302

    def test_get_urls(self, jira_connection_admin):
        urls = jira_connection_admin.get_urls()
        assert urls[0].name == 'planning_poker_jira_jiraconnection_import_stories'

    @pytest.mark.parametrize('obj', [None, JiraConnection('foo', 'https://test.com', 'username', 'password', 'field')])
    def test_get_fields(self, obj, jira_connection_admin):
        fields = jira_connection_admin.get_fields(None, obj)
        if obj:
            expected_result = ('label', 'api_url', 'username', ('password', 'delete_password'), 'story_points_field',
                               'test_connection')
        else:
            expected_result = ('label', 'api_url', 'username', 'password', 'story_points_field', 'test_connection')
        assert fields == expected_result

    def test_get_import_stories_url(self, jira_connection, jira_connection_admin):
        import_stories_tag = jira_connection_admin.get_import_stories_url(jira_connection)
        assert import_stories_tag == '<a href="/admin/planning_poker_jira/jiraconnection/1/import_stories/">Import</a>'
