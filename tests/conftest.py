from datetime import datetime
import pytest
from unittest.mock import patch

from planning_poker.models import PokerSession
from planning_poker_jira.forms import ExportStoriesForm, ImportStoriesForm, JiraAuthenticationForm, JiraConnectionForm
from planning_poker_jira.models import JiraConnection


@pytest.fixture
def jira_connection(db):
    return JiraConnection.objects.create(api_url='http://test_url', username='testuser', story_points_field='testfield')


@pytest.fixture
def poker_session(db):
    return PokerSession.objects.create(poker_date=datetime.now(), name='test session')


@pytest.fixture
def form_data():
    return {
        'username': 'testuser',
        'password': 'supersecret'
    }


@pytest.fixture
@patch('planning_poker_jira.models.JIRA')
def jira_authentication_form(form_data):
    return JiraAuthenticationForm(form_data)


@pytest.fixture
@patch('planning_poker_jira.models.JIRA')
def jira_connection_form(form_data):
    form_data['api_url'] = 'https://test'
    return JiraConnectionForm(form_data)


@pytest.fixture
@patch('planning_poker_jira.models.JIRA')
def export_stories_form(form_data, jira_connection):
    form_data['jira_connection'] = jira_connection
    return ExportStoriesForm(form_data)


@pytest.fixture
@patch('planning_poker_jira.models.JIRA')
def import_stories_form(form_data, jira_connection, poker_session):
    form_data['poker_session'] = poker_session
    form_data['jql_query'] = 'Sprint = "1"'
    return ImportStoriesForm(jira_connection, form_data)

