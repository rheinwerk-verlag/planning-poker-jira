from datetime import datetime

import pytest

from planning_poker.models import PokerSession, Story
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
