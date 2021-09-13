from django.utils.translation import gettext, gettext_lazy as _
from jira.exceptions import JIRAError
from requests.exceptions import ConnectionError, RequestException


def get_error_text(exception: Exception, **context) -> str:
    """Utility method which returns a string explaining the given exception.

    :param exception: The exception which should be explained.
    :param context: The context which was present when the exception was raised.
    :return: A string explaining the given jira error.
    """
    if isinstance(exception, JIRAError):
        error_text = get_jira_error_error_text(exception, **context)
    elif isinstance(exception, ConnectionError):
        error_text = gettext('Failed to connect to server.')
        api_url = context.get('api_url')
        if api_url:
            error_text = ' '.join((error_text, gettext('Is "{api_url}" the correct API URL?').format(api_url=api_url)))
    elif isinstance(exception, RequestException):
        error_text = _('There was an ambiguous error with your request. Check if all your data is correct.')
    else:
        error_text = _('Encountered an unknown exception.')
    return error_text


def get_jira_error_error_text(jira_error: JIRAError, **context) -> str:
    """Utility method which returns a string explaining the given jira error.

    :param jira_error: The jira error which should be explained.
    :param context: The context which was present when the exception was raised.
    :return: A string explaining the given jira error.
    """
    if jira_error.status_code == 400:
        # A bad request usually means that the jql query string was ill-formed. However, JIRA actually returns a
        # presentable response explaining the error which can be passed directly to the user.
        error_text = jira_error.text
    elif jira_error.status_code == 401:
        error_text = _('Could not authenticate the API user with the given credentials. '
                       'Make sure that you entered the correct data.')
    elif jira_error.status_code == 404:
        connection = context.get('connection')
        if connection:
            error_text = _('The story does probably not exist inside "{connection}".').format(connection=connection)
        else:
            error_text = _('The story does probably not exist inside the selected backend.')
    else:
        error_text = _('Received status code {status_code}.').format(status_code=jira_error.status_code)
    return error_text
