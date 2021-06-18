from datetime import datetime
from unittest.mock import patch

import pytest
from django.contrib.admin.sites import site
from django.forms.models import modelform_factory

from planning_poker.models import PokerSession, Story

from planning_poker_jira.admin import JiraConnectionAdmin
from planning_poker_jira.forms import JiraAuthenticationForm, JiraConnectionForm
from planning_poker_jira.models import JiraConnection


@pytest.fixture
def jira_connection(db):
    return JiraConnection.objects.create(api_url='http://test_url', username='testuser', story_points_field='testfield',
                                         password='supersecret')


@pytest.fixture
def poker_session(db):
    return PokerSession.objects.create(poker_date=datetime.now(), name='test session')


@pytest.fixture
def stories(db):
    stories = [
        {
            'ticket_number': 'FIAE-1',
            'title': 'Write tests',
            'description': 'Tests need to be written.',
            '_order': 0
        },
        {
            'ticket_number': 'FIAE-2',
            'title': 'Write more tests',
            'description': 'More tests need to be written.',
            '_order': 1
        }
    ]
    return Story.objects.bulk_create([Story(**story) for story in stories])


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


@pytest.fixture(params=['http://different.url', ''])
def form_data_api_url(request):
    return {'api_url': request.param}


@pytest.fixture
def expected_api_url(form_data_api_url, jira_connection):
    return {'api_url': form_data_api_url.get('api_url') or jira_connection.api_url}


@pytest.fixture
@patch('planning_poker_jira.models.JIRA')
def jira_authentication_form(form_data):
    return JiraAuthenticationForm(form_data)


@pytest.fixture
def jira_connection_form_class():
    return modelform_factory(JiraConnection, form=JiraConnectionForm, fields='__all__', exclude=())


@pytest.fixture
def jira_connection_admin():
    return JiraConnectionAdmin(JiraConnection, site)


@pytest.fixture
def export_stories_form_data(form_data, jira_connection):
    return dict(**form_data, jira_connection=jira_connection.pk)
