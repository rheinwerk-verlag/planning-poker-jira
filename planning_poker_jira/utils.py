from django.utils.translation import gettext_lazy as _
from jira.exceptions import JIRAError

from planning_poker.models import Story

from .models import JiraConnection


def get_jira_error_error_text(jira_error: JIRAError, connection: JiraConnection = None) -> str:
    """Utility method which returns a string explaining the given jira error.

    :param JIRAError jira_error: The jira error which should be explained.
    :param JiraConnection connection: The connection which was involved in raising the jira error.
    :return: A string explaining the given jira error.
    :rtype: str
    """
    if jira_error.status_code == 400:
        # A bad request usually means that the jql query string was ill-formed. However, JIRA actually returns a
        # presentable response explaining the error which can be passed directly to the user.
        error_text = jira_error.text
    elif jira_error.status_code == 401:
        error_text = _('Could not authenticate the API user with the given credentials. '
                       'Make sure that you entered the correct data.')
    elif jira_error.status_code == 404:
        error_text = _('The story does probably not exist inside "{}"').format(connection)
    else:
        error_text = _('Received status code {}').format(jira_error.status_code)
    return error_text
