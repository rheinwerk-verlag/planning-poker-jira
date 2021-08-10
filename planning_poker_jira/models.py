# -*- coding: utf-8 -*
import logging
from typing import List, Optional

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from encrypted_fields import fields
from jira import JIRA

from planning_poker.models import PokerSession, Story

logger = logging.getLogger(__name__)


class JiraConnection(models.Model):
    #: Used solely for displaying the Jira Connection to the user.
    label = models.CharField(verbose_name=_('Label'), max_length=200, blank=True)
    #: The API URL used for making requests to the Jira backend.
    api_url = models.CharField(verbose_name=_('API URL'), max_length=200)
    #: The username used for the authentication at the API.
    username = models.CharField(verbose_name=_('API Username'), max_length=200, blank=True)
    #: The password used for the authentication at the API.
    password = fields.EncryptedCharField(verbose_name=_('Password'), max_length=200, blank=True)
    #: The name of the field the Jira backend uses to store the story points.
    story_points_field = models.CharField(verbose_name=_('Story Points Field'), max_length=200)

    class Meta:
        verbose_name = _('Jira Connection')
        verbose_name_plural = _('Jira Connections')

    def __str__(self) -> str:
        return self.label or self.api_url

    def get_client(self) -> JIRA:
        """Authenticate at the jira backend and return a client to communicate with it."""
        return JIRA(self.api_url, basic_auth=(self.username, self.password),
                    timeout=getattr(settings, 'JIRA_TIMEOUT', (3.05, 7)),
                    max_retries=getattr(settings, 'JIRA_NUM_RETRIES', 0))

    def create_stories(self, query_string: str, poker_session: Optional[PokerSession] = None,
                       client: Optional[JIRA] = None) -> List[Story]:
        """Fetch issues from the Jira client with the given query string and add them to the poker session.

        :param query_string: The string which should be used to query the stories.
        :param poker_session: The poker session to which the stories should be added.
        :param client: The jira client which should be used to import the stories. Optional.
        :return: A list containing the created stories.
        """

        results = (client or self.get_client()).search_issues(
            jql_str=query_string,
            expand='renderedFields',
            fields=['summary', 'description']
        )
        order_start = getattr(poker_session.stories.last(), '_order', -1) + 1 if poker_session else 0
        stories = [Story(
            ticket_number=story.key, title=story.fields.summary,
            description=story.renderedFields.description, poker_session=poker_session,
            _order=index
        ) for index, story in enumerate(results, start=order_start)]
        return Story.objects.bulk_create(stories)
