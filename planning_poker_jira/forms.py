from typing import Any, Dict

from django import forms
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
    #: The username used for the authentication at the API.
    username = forms.CharField(label=_('Username'),
                               help_text=_('You can use this to override the username saved in the database'),
                               required=False)
    #: The password used for the authentication at the API.
    password = forms.CharField(label=_('Password'),
                               help_text=_('You can use this to override the password in the database'),
                               required=False,
                               widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self._client = None
        super().__init__(*args, **kwargs)

    @property
    def client(self) -> JIRA:
        """A client which can be used to communicate with the jira backend. E.g. to import/export stories.
        This property only becomes available when the form was configured to test the connection and after the form was
        successfully validated.

        Use this whenever you want to communicate with the jira backend in order to prevent multiple authentication
        requests during the handling of the same form.

        :param: A `JIRA` instance which can be used to communicate with the jira backend.
        """
        if self._client is None:
            raise ValueError('Could not get the client because either the data did not validate or because this form '
                             'was not configured to test the connection')
        return self._client

    def _get_connection(self) -> JiraConnection:
        """This method should be implemented by all the child classes in order to provide a `JiraConnection` instance.
        The provided `JiraConnection` is used during the form's validation process.

        The returned instance does not have to be a saved instance from the database.

        :return: A `JiraConnection` which can be used to retrieve a `JIRA` instance.
        """
        raise NotImplementedError()  # pragma: no cover

    def _requires_connection_test(self) -> bool:
        """Determine whether the connection to the jira backend should be tested.
        This method gets called during the form's validation process in order to determine whether the connection should
        be tested and therefore *whether the `client` property will be populated or not*.

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
    #: Determines whether the connection should be tested.
    test_connection = forms.BooleanField(label=_('Test Connection'),
                                         help_text=_('Check this if you want to test your entered data and try to '
                                                     'authenticate against the API'),
                                         required=False)
    #: Determines whether the saved password should be deleted.
    delete_password = forms.BooleanField(label=_('Delete Password'),
                                         help_text=_('Check this if you want to delete your saved password'),
                                         required=False)

    class Meta:
        model = JiraConnection
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['password'].help_text = _('Use this to override the password or leave it blank to make no changes')

    def clean(self):
        cleaned_data = self.cleaned_data
        # This form requires some extra handling while cleaning. Since the password field will not be prepopulated with
        # data from the database, the password would be reset to an empty string whenever the user wants to change any
        # attribute for an existing `JiraConnection` instance without reentering the password. The form interprets
        # an empty password field as no changes to the password to circumvent that. In order for the user to be still be
        # able to delete a saved password, the `delete_password` field was added which indicates whether the password
        # should be deleted or not.
        delete_password = cleaned_data.get('delete_password')
        if delete_password and cleaned_data['password']:
            self.add_error('password', _('You can not change the password and delete it at the same time'))
            return cleaned_data
        elif delete_password:
            cleaned_data['password'] = ''
        else:
            cleaned_data['password'] = cleaned_data['password'] or self.instance.password

        return super().clean()

    def _get_connection(self) -> JiraConnection:
        return JiraConnection(api_url=self.cleaned_data.get('api_url'),
                              username=self.cleaned_data.get('username'),
                              password=self.cleaned_data.get('password'))

    def _requires_connection_test(self) -> bool:
        # Determine whether the connection to the jira backend should be tested. This depends on the `test_connection`
        # checkbox. Since it is optional for the user to save their password inside the database, it is not always
        # possible to test the connection. Especially because an empty password field means that the currently saved
        # password shouldn't be changed.
        return self.cleaned_data['test_connection']


class ExportStoryPointsForm(JiraAuthenticationForm):
    """Form which is used for exporting stories to the jira backend."""
    #: The Jira backend you want to export the story points to.
    jira_connection = forms.ModelChoiceField(
        label=_('Jira Connection'),
        help_text=_('The Jira Backend to which the story points should be exported. The points for any stories which '
                    'are not present in the backend can not be exported'),
        queryset=JiraConnection.objects.all(),
        required=True
    )

    def _get_connection(self) -> JiraConnection:
        connection = self.cleaned_data['jira_connection']
        return JiraConnection(api_url=connection.api_url,
                              username=self.cleaned_data['username'] or connection.username,
                              password=self.cleaned_data['password'] or connection.password)


class ImportStoriesForm(JiraAuthenticationForm):
    """Form which is used for importing stories from the jira backend."""
    #: Optional: The poker session to which you want to import the stories.
    poker_session = forms.ModelChoiceField(
        label=_('Poker Session'),
        help_text=_('The poker session to which the imported stories should be added'),
        queryset=PokerSession.objects.all(),
        required=False
    )
    #: The query which should be used to retrieve the stories from the Jira backend.
    jql_query = forms.CharField(label=_('JQL Query'), required=True)

    def __init__(self, connection: JiraConnection, *args, **kwargs):
        """The `ImportStoriesForm` requires a `JiraConnection` passed from the outside in order to use it to acquire
        fallback data for the `_get_connection()` method.

        :param connection: The connection which will be used to acquire fallback data.
        :param args: Additional arguments which will be passed to the parent's constructor.
        :param kwargs: Additional keyword arguments which will be passed to the parent's constructor.
        """
        super().__init__(*args, **kwargs)
        self._connection = connection

    def _get_connection(self) -> JiraConnection:
        return JiraConnection(api_url=self._connection.api_url,
                              username=self.cleaned_data['username'] or self._connection.username,
                              password=self.cleaned_data['password'] or self._connection.password)
