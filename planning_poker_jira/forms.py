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
        self._connection = kwargs.pop('connection', None)
        super().__init__(*args, **kwargs)

    @cached_property
    def client(self) -> JIRA:
        if self.errors:
            raise ValueError('Could not get the client because the data did not validate')
        if self.connection:
            client = self.connection.get_client()
        else:
            client = JIRA(self.cleaned_data.get('api_url'),
                          basic_auth=(self.cleaned_data.get('username'), self.cleaned_data.get('password')))
        return client

    @cached_property
    def connection(self) -> JiraConnection:
        if self.errors:
            raise ValueError('Could not get the connection because the data did not validate')
        return self.cleaned_data.get('jira_connection') or self._connection or self.instance

    def clean(self) -> dict:
        cleaned_data = super().clean()

        api_url = cleaned_data.get('api_url') or getattr(self.connection, 'api_url', None)
        username = cleaned_data.get('username') or getattr(self.connection, 'username', None)
        # We override `cleaned_data['password']` because it would otherwise reset the model's password to an empty
        # string if the user didn't enter anything in the form's password field.
        password = cleaned_data['password'] = cleaned_data.get('password') or getattr(self.connection, 'password', None)
        if not (api_url and username):
            self.add_error(None,
                           _('Missing credentials. Check whether you entered an API URL, an username and a password'))
        # We don't have to verify the credentials if the user hasn't provided a password.
        if password:
            try:
                JIRA(api_url, basic_auth=(username, password))
            except JIRAError as e:
                self.add_error(None, get_jira_error_error_text(e))
            except ConnectionError:
                self.add_error(None, _('Failed to connect to server. Is "{}" the correct API URL?').format(api_url))
            except RequestException:
                self.add_error(None,
                               _('There was an ambiguous error with your request. Check if all your data is correct.'))
        return cleaned_data


class JiraConnectionForm(JiraAuthenticationForm, forms.ModelForm):
    username = forms.CharField(label=_('Username'),
                               required=False)
    password = forms.CharField(label=_('Password'),
                               required=False,
                               widget=forms.PasswordInput)


class ImportStoriesForm(JiraAuthenticationForm):
    poker_session = forms.ModelChoiceField(
        label=_('Poker Session'),
        help_text=_('The poker session to which the imported stories should be added'),
        queryset=PokerSession.objects.all(),
        required=False
    )
    jql_query = forms.CharField(label=_('JQL Query'), required=True)


class ExportStoriesForm(JiraAuthenticationForm):
    jira_connection = forms.ModelChoiceField(
        label=_('Jira Connection'),
        help_text=_('The Jira Backend to which the stories should be exported'),
        queryset=JiraConnection.objects.all(),
        required=True
    )
