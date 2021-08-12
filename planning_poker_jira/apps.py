from channels_presence.apps import RoomsConfig
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PlanningPokerJiraConfig(AppConfig):
    name = 'planning_poker_jira'
    verbose_name = _('Planning Poker: Jira Extension')


class ChannelsPresenceConfig(RoomsConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'channels_presence'
    verbose_name = _('Channels Presence')
