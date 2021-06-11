from requests.exceptions import ConnectionError, RequestException

from django import forms
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from jira import JIRA, JIRAError

from planning_poker.models import PokerSession

from .models import JiraConnection
from .utils import get_jira_error_error_text


class JiraAuthenticationForm(forms.Form):
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
        """A client which can be used to communicate with the jira backend. E.g. to import/export stories."""
        if self._client is None:
            raise ValueError('Could not get the client because the data did not validate')
        return self._client

    def _get_connection(self) -> JiraConnection:
        """This method should be implemented by all the child classes in order to provide a JiraConnection instance."""
        raise NotImplementedError()

    def clean(self) -> dict:
        cleaned_data = super().clean()
        connection = self._get_connection()
        # We override `cleaned_data['password']` because it would otherwise reset the model's password to an empty
        # string if the user didn't enter anything in the form's password field.
        cleaned_data['password'] = connection.password
        if not (connection.api_url and connection.username):
            self.add_error(None,
                           _('Missing credentials. Check whether you entered an API URL, and a username.'))
        try:
            self._client = connection.get_client()
        except JIRAError as e:
            self.add_error(None, get_jira_error_error_text(e))
        except ConnectionError:
            self.add_error(None, _('Failed to connect to server. Is "{}" the correct API URL?')
                           .format(connection.api_url))
        except RequestException:
            self.add_error(None,
                           _('There was an ambiguous error with your request. Check if all your data is correct.'))
        return cleaned_data


class JiraConnectionForm(JiraAuthenticationForm, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['password'].help_text = None

    def _get_connection(self) -> JiraConnection:
        """Create a JiraConnection instance from the form data."""
        return JiraConnection(**self.cleaned_data)


class ImportStoriesForm(JiraAuthenticationForm):
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
        """Return a JiraConnection instance where the username and password can be overridden by the form."""
        return JiraConnection(api_url=self._connection.api_url,
                              username=self.cleaned_data['username'] or self._connection.username,
                              password=self.cleaned_data['password'] or self._connection.password)


class ExportStoriesForm(JiraAuthenticationForm):
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
