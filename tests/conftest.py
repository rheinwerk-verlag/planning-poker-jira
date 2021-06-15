from datetime import datetime
import pytest
from unittest.mock import patch

from django.forms.models import modelform_factory

from planning_poker.models import PokerSession
from planning_poker_jira.forms import ExportStoriesForm, ImportStoriesForm, JiraAuthenticationForm, JiraConnectionForm
from planning_poker_jira.models import JiraConnection


@pytest.fixture
def jira_connection(db):
    return JiraConnection.objects.create(api_url='http://test_url', username='testuser', story_points_field='testfield',
                                         password='supersecret')


@pytest.fixture
def poker_session(db):
    return PokerSession.objects.create(poker_date=datetime.now(), name='test session')


@pytest.fixture
def form_data():
    return {
        'username': 'testuser',
        'password': 'supersecret'
    }


@pytest.fixture(params=['different_testuser', ''])
def form_data_username(request):
    return {'username': request.param}


@pytest.fixture
def expected_username(form_data_username, jira_connection):
    return {'username': form_data_username.get('username') or jira_connection.username}


@pytest.fixture(params=['evenmoresupersecret', ''])
def form_data_password(request):
    return {'password': request.param}


@pytest.fixture
def expected_password(form_data_password, jira_connection):
    return {'password': form_data_password.get('password') or jira_connection.password}


@pytest.fixture
@patch('planning_poker_jira.models.JIRA')
def jira_authentication_form(form_data):
    return JiraAuthenticationForm(form_data)


@pytest.fixture
def jira_connection_form_class():
    return modelform_factory(JiraConnection, form=JiraConnectionForm, fields='__all__', exclude=())
