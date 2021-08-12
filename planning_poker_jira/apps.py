from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PlanningPokerJiraConfig(AppConfig):
    default = True
    default_auto_field = 'django.db.models.AutoField'
    name = 'planning_poker_jira'
    verbose_name = _('Planning Poker: Jira Extension')
