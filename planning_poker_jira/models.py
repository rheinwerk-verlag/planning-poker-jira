# -*- coding: utf-8 -*
import logging
from urllib.parse import urljoin

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from jira import JIRA, JIRAError

from planning_poker.models import Story

logger = logging.getLogger(__name__)


class JiraConnection(models.Model):
    api_url = models.CharField(verbose_name=_('API Url'), max_length=200)
    username = models.CharField(verbose_name=_('API Username'), max_length=200)
    story_points_field = models.CharField(verbose_name=_('Story Points Field'), max_length=200)

    class Meta:
        verbose_name = _('Jira Connection')
        verbose_name_plural = _('Jira Connections')

    def __str__(self):
        return self.api_url

    def client(self, password):
        return JIRA(self.api_url, basic_auth=(self.username, password))

    def create_stories(self, query_string, poker_session, password):
        """Fetch issues from the Jira client with the given query string and add them to the poker session.

        :param str query_string: The string which should be used to query the stories.
        :param planning_poker.models.PokerSession poker_session: The poker session to which the stories should be added.
        :param str password: The password used to authenticate the jira api user.
        """
        try:
            results = self.client(password).search_issues(
                jql_str=query_string,
                expand='renderedFields',
                fields=['summary', 'description']
            )
        except JIRAError as e:
            logger.warning(e)
        else:
            with transaction.atomic():
                for story in results:
                    JiraStory.objects.create(
                        ticket_number=story.key,
                        title=story.fields.summary,
                        description=story.renderedFields.description,
                        poker_session=poker_session,
                        jira_instance=self
                    )


class JiraStory(Story):
    jira_instance = models.ForeignKey(JiraConnection, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _('Jira Story')
        verbose_name_plural = _('Jira Stories')

    def url(self):
        return urljoin(self.jira_instance.api_url, 'browse/' + self.ticket_number)
