from datetime import datetime
import pytest

from planning_poker.models import PokerSession
from planning_poker_jira.models import JiraConnection


@pytest.fixture
def jira_connection(db):
    return JiraConnection.objects.create(api_url='http://test_url', username='testuser', story_points_field='testfield')


@pytest.fixture
def poker_session(db):
    return PokerSession.objects.create(poker_date=datetime.now(), name='test session')
