from contextlib import nullcontext as does_not_raise
from unittest.mock import Mock, patch

import pytest
from jira import JIRAError


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
    def test_get_client(self, mock_jira, jira_connection):
        jira_connection.get_client()
        mock_jira.assert_called_with(jira_connection.api_url, basic_auth=(jira_connection.username,
                                                                          jira_connection.password))

    @patch('planning_poker_jira.models.JIRA')
    @pytest.mark.parametrize('expected_exception, side_effect, expected_result', [
        (pytest.raises(JIRAError), JIRAError(), []),
        (does_not_raise(),
         [[
            JiraTestStory(fields={'summary': 'write tests'}, rendered_fields={'description': 'foo'}, key='FIAE-1'),
            JiraTestStory(fields={'summary': 'more tests'}, rendered_fields={'description': 'bar'}, key='FIAE-2')
         ]],
         [
            {'ticket_number': 'FIAE-1', 'title': 'write tests', 'description': 'foo'},
            {'ticket_number': 'FIAE-2', 'title': 'more tests', 'description': 'bar'}
         ])
    ])
    def test_create_stories(self, mock_jira, expected_exception, side_effect, expected_result, jira_connection,
                            poker_session):
        mock_client = Mock()
        mock_jira.return_value = mock_client
        mock_client.search_issues.side_effect = side_effect

        with expected_exception:
            jira_connection.create_stories('project=FIAE', poker_session)
        assert list(poker_session.stories.values('ticket_number', 'title', 'description')) == expected_result
        mock_client.search_issues.assert_called_with(
            jql_str='project=FIAE',
            expand='renderedFields',
            fields=['summary', 'description']
        )
