from typing import Any, Dict

from django import forms
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from jira import JIRA, JIRAError
from requests.exceptions import ConnectionError, RequestException

from planning_poker.models import PokerSession

from .models import JiraConnection
from .utils import get_error_text


class JiraAuthenticationForm(forms.Form):
    """Base class for all the forms which handle jira connections.
    All derived forms provide a way to communicate with the jira backend through the `client` property.
    """
    username = forms.CharField(label=_('Username'),
                               help_text=_('You can use this to override the username saved in the database'),
                               required=False)
    password = forms.CharField(label=_('Password'),
                               help_text=_('You can use this to override the password in the database'),
                               required=False,
                               widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self._client = None
        super().__init__(*args, **kwargs)

    @cached_property
    def client(self) -> JIRA:
        """A client which can be used to communicate with the jira backend. E.g. to import/export stories.
        This property only becomes available when the form was configured to test the connection and after the form was
        successfully validated.

        Use this whenever you want to communicate with the jira backend in order to prevent multiple authentication
        requests during the handling of the same form.

        :param: A `JIRA` instance which can be used to communicate with the jira backend.
        """
        if self._client is None:
            error_message = 'Could not get the client because {reason}'
            if self._requires_connection_test():
                error_message = error_message.format(reason='the data did not validate')
            else:
                error_message = error_message.format(reason='`test_connection` returned `False`')
            raise ValueError(error_message)
        return self._client

    def _get_connection(self) -> JiraConnection:
        """This method should be implemented by all the child classes in order to provide a `JiraConnection` instance.
        The provided `JiraConnection` is used during the form's validation process.

        The returned instance does not have to be a saved instance from the database.

        :return: A `JiraConnection` which can be used to retrieve a `JIRA` instance.
        """
        raise NotImplementedError()

    def _requires_connection_test(self) -> bool:
        """Determine whether the connection to the jira backend should be tested.
        This method gets called during the form's validation process in order to determine whether the connection should
        be tested and therefore _whether the `client` property will be populated or not_.

        Since most use cases require the connection to be tested this implementation will always return `True`.
        Child classes however can override this method to make the test optional (see the class`JiraConnectionForm`
        for an example) if needed.

        :return: Whether the connection should be tested.
        """
        return True

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        connection = self._get_connection()
        if self._requires_connection_test():
            if not (connection.api_url and connection.username):
                self.add_error(None, _('Missing credentials. Check whether you entered an API URL, and a username.'))
            else:
                try:
                    self._client = connection.get_client()
                except (JIRAError, ConnectionError, RequestException) as e:
                    self.add_error(None, get_error_text(e, api_url=connection.api_url, connection=connection))
        return cleaned_data


class JiraConnectionForm(JiraAuthenticationForm, forms.ModelForm):
    """Form which is used for the `JiraConnectionAdmin` class. This is used for the change and create views."""
    test_connection = forms.BooleanField(label=_('Test Connection'),
                                         help_text=_('Check this if you want to test your entered data and try to '
                                                     'authenticate against the API'),
                                         required=False)
    delete_password = forms.BooleanField(label=_('Delete Password'),
                                         help_text=_('Check this if you want to delete your saved password'),
                                         required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['password'].help_text = None

    def clean(self):
        cleaned_data = self.cleaned_data
        # This form requires some extra handling while cleaning. Since the password field will not be prepopulated with
        # data from the database, the password would be reset to an empty string whenever the user wants to change any
        # attribute for an existing `JiraConnection` instance without reentering the password. The form interprets
        # an empty password field as no changes to the password to circumvent that. In order for the user to be still be
        # able to delete a saved password, we added the `delete_password` field which indicates whether the password
        # should be deleted or not.
        delete_password = cleaned_data.get('delete_password')
        if delete_password and cleaned_data['password']:
            self.add_error('password', _('You can not change the password and delete it at the same time'))
        elif delete_password:
            cleaned_data['password'] = ''
        else:
            cleaned_data['password'] = cleaned_data['password'] or self.instance.password

        return super().clean()

    def _get_connection(self) -> JiraConnection:
        """Create a JiraConnection instance from the form data."""
        return JiraConnection(api_url=self.cleaned_data.get('api_url') or self.instance.api_url,
                              username=self.cleaned_data.get('username') or self.instance.username,
                              password=self.cleaned_data.get('password'))

    def _requires_connection_test(self) -> bool:
        """Determine whether the connection to the jira backend should be tested.
        This depends on the `test_connection` checkbox and on potential form errors which occur when the
        `delete_password` checkbox has been checked while a new password has also been provided.
        Since it is optional for the user to save their password inside the database, it is not always possible to test
        the connection. Especially because an empty password field means that the currently saved password shouldn't be
        changed.

        :return: Whether the connection should be tested.
        """
        return self.cleaned_data['test_connection'] and not self.has_error('password')


class ExportStoriesForm(JiraAuthenticationForm):
    """Form which is used for exporting stories to the jira backend."""
    jira_connection = forms.ModelChoiceField(
        label=_('Jira Connection'),
        help_text=_('The Jira Backend to which the stories should be exported'),
        queryset=JiraConnection.objects.all(),
        required=True
    )

    def _get_connection(self) -> JiraConnection:
        """Return a JiraConnection instance where the username and password can be overridden by the form."""
        connection = self.cleaned_data['jira_connection']
        return JiraConnection(api_url=connection.api_url,
                              username=self.cleaned_data['username'] or connection.username,
                              password=self.cleaned_data['password'] or connection.password)


class ImportStoriesForm(JiraAuthenticationForm):
    """Form which is used for importing stories from the jira backend."""
    poker_session = forms.ModelChoiceField(
        label=_('Poker Session'),
        help_text=_('The poker session to which the imported stories should be added'),
        queryset=PokerSession.objects.all(),
        required=False
    )
    jql_query = forms.CharField(label=_('JQL Query'), required=True)

    def __init__(self, connection, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connection = connection

    def _get_connection(self) -> JiraConnection:
        """Return a `JiraConnection` instance where the username and password can be overridden by the form."""
        return JiraConnection(api_url=self._connection.api_url,
                              username=self.cleaned_data['username'] or self._connection.username,
                              password=self.cleaned_data['password'] or self._connection.password)
