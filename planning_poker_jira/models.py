# -*- coding: utf-8 -*
import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from encrypted_fields import fields
from jira import JIRA, JIRAError

from planning_poker.models import Story

logger = logging.getLogger(__name__)


class JiraConnection(models.Model):
    label = models.CharField(verbose_name=_('Label'), max_length=200, null=True, blank=True)
    api_url = models.CharField(verbose_name=_('API URL'), max_length=200)
    username = models.CharField(verbose_name=_('API Username'), max_length=200, null=True, blank=True)
    password = fields.EncryptedCharField(verbose_name=_('Password'), max_length=200, null=True, blank=True)
    story_points_field = models.CharField(verbose_name=_('Story Points Field'), max_length=200)

    class Meta:
        verbose_name = _('Jira Connection')
        verbose_name_plural = _('Jira Connections')

    def __str__(self) -> str:
        return self.label or self.api_url

    def get_client(self, username=None, password=None) -> JIRA:
        """Authenticate at the jira backend and return a client to communicate with it.

        :param str username: The name of the user who should be authenticated. Default None.
        :param str password: The password used to authenticate the user. Default None.
        """
        return JIRA(self.api_url, basic_auth=(username or self.username, password or self.password))

    def create_stories(self, query_string, poker_session, password) -> None:
        """Fetch issues from the Jira client with the given query string and add them to the poker session.

        :param str query_string: The string which should be used to query the stories.
        :param planning_poker.models.PokerSession poker_session: The poker session to which the stories should be added.
        :param str password: The password used to authenticate the jira api user.
        """
        try:
            results = self.get_client(password=password).search_issues(
                jql_str=query_string,
                expand='renderedFields',
                fields=['summary', 'description']
            )
        except JIRAError as e:
            logger.warning(e)
        else:
            Story.objects.bulk_create([Story(ticket_number=story.key, title=story.fields.summary,
                                             description=story.renderedFields.description, poker_session=poker_session,
                                             _order=index)
                                       for index, story in enumerate(results)])
