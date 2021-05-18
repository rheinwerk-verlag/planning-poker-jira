from unittest.mock import Mock, patch

import pytest
from jira import JIRAError

from planning_poker_jira.models import JiraConnection


class JiraFields:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)


class JiraTestStory:
    def __init__(self, fields, rendered_fields, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)
        self.fields = JiraFields(**fields)
        self.renderedFields = JiraFields(**rendered_fields)


class TestJiraConnection:
    @patch('planning_poker_jira.models.JIRA')
    def test_client(self, mock_jira, jira_connection):
        password = 'supersecret'
        jira_connection.get_client(password=password)
        mock_jira.assert_called_with(jira_connection.api_url, basic_auth=(jira_connection.username, password))

    @patch('planning_poker_jira.models.JIRA')
    @pytest.mark.parametrize('jira_error, side_effect', [
        (True, JIRAError()),
        (False, [[
            JiraTestStory(fields={'summary': 'write tests'}, rendered_fields={'description': 'foo'}, key='FIAE-1'),
            JiraTestStory(fields={'summary': 'more tests'}, rendered_fields={'description': 'bar'}, key='FIAE-2')
        ]])
    ]
    )
    def test_get_poker_stories(self, mock_jira, jira_error, side_effect, jira_connection, poker_session):
        mock_client = Mock()
        mock_jira.return_value = mock_client
        mock_client.search_issues.side_effect = side_effect
        expected_result = [] if jira_error else [
            {'number': 'FIAE-1', 'title': 'write tests', 'description': 'foo'},
            {'number': 'FIAE-2', 'title': 'more tests', 'description': 'bar'}
        ]

        jira_connection.create_stories('project=FIAE', poker_session, 'supersecret')
        assert list(poker_session.stories.values_list('ticket_number', flat=True)) == [story['number'] for story in
                                                                                       expected_result]
        mock_client.search_issues.assert_called_with(
            jql_str='project=FIAE',
            expand='renderedFields',
            fields=['summary', 'description']
        )
