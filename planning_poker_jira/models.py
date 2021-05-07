# -*- coding: utf-8 -*
import logging
from urllib.parse import urljoin

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from jira import JIRA, JIRAError

from planning_poker.models import Story

logger = logging.getLogger(__name__)


class JiraConnection(models.Model):
    api_url = models.CharField(verbose_name=_('API Url'))
    username = models.CharField(verbose_name=_('API Username'))
    password = models.CharField(verbose_name=_('API Password'))
    story_points_field = models.CharField(verbose_name=_('Story Points Field'))

    class Meta:
        verbose_name = _('Jira Connection')
        verbose_name_plural = _('Jira Connections')

    def __str__(self):
        return self.api_url

    @cached_property
    def client(self):
        return JIRA(self.api_url, basic_auth=(self.username, self.password))

    def create_stories(self, query_string, poker_session):
        try:
            results = self.client.search_issues(
                jql_str=query_string,
                expand='renderedFields',
                fields=['summary', 'description']
            )
        except JIRAError as e:
            logger.warning(e)
        else:
            JiraStory.objects.bulk_create([
                JiraStory(
                    number=story.key,
                    title=story.fields.summary,
                    description=story.renderedFields.description,
                    poker_session=poker_session,
                    jira_instance=self
                )
                for story in results
            ])


class JiraStory(Story):
    jira_instance = models.ForeignKey(JiraConnection, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _('Jira Story')
        verbose_name_plural = _('Jira Stories')

    def url(self):
        return urljoin(self.jira_instance.api_url, 'browse/' + self.ticket_number)
