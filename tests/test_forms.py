from contextlib import nullcontext as does_not_raise
import pytest
from requests.exceptions import ConnectionError, RequestException
from unittest.mock import Mock, patch

from jira import JIRAError

from planning_poker_jira.forms import ExportStoriesForm, ImportStoriesForm, JiraAuthenticationForm, JiraConnectionForm
from planning_poker_jira.models import JiraConnection


class TestJiraAuthenticationForm:
    def test_init(self):
        form = JiraAuthenticationForm()
        assert form._client is None

    @pytest.mark.parametrize('cleaned, expected', (
        (True, does_not_raise()),
        (False, pytest.raises(ValueError))
    ))
    def test_client(self, jira_authentication_form, cleaned, expected, jira_connection):
        mock_get_connection = Mock(return_value=jira_connection)

        with patch.object(jira_authentication_form, '_get_connection', mock_get_connection):
            with patch.object(jira_connection, 'get_client'):
                if cleaned:
                    jira_authentication_form.is_valid()
                    jira_authentication_form.clean()
                with expected:
                    jira_authentication_form.client

    @pytest.mark.parametrize('form_data, num_expected_missing_credentials_errors', (
        ({'api_url': None, 'username': None}, 1),
        ({'api_url': 'https://test', 'username': None}, 1),
        ({'api_url': None, 'username': 'testuser'}, 1),
        ({'api_url': 'https://test', 'username': 'testuser'}, 0),
    ))
    @pytest.mark.parametrize('side_effect, num_expected_side_effects_errors', (
        (JIRAError(), 1),
        (ConnectionError(), 1),
        (RequestException(), 1),
        (None, 0),
    ))
    def test_clean(self, form_data, num_expected_missing_credentials_errors, side_effect,
                   num_expected_side_effects_errors, jira_connection):
        mock_get_connection = Mock(return_value=jira_connection)
        mock_get_client = Mock(side_effect=side_effect)
        jira_authentication_form = JiraAuthenticationForm()
        jira_authentication_form.cleaned_data = {}
        for attribute, value in form_data.items():
            setattr(jira_connection, attribute, value)

        with patch.object(jira_authentication_form, '_get_connection', mock_get_connection):
            with patch.object(jira_connection, 'get_client', mock_get_client):
                cleaned_data = jira_authentication_form.clean()

        num_generated_errors = len(jira_authentication_form.errors.get('__all__', []))
        assert num_generated_errors == num_expected_missing_credentials_errors + num_expected_side_effects_errors
        assert cleaned_data['password'] == jira_connection.password


class TestJiraConnectionForm:
    def test_init(self):
        class Meta:
            model = JiraConnection
        JiraConnectionForm._meta = Meta
        form = JiraConnectionForm()
        assert form._client is None
        assert form.fields['username'].help_text is None
        assert form.fields['password'].help_text is None

    @pytest.mark.parametrize('form_data_api_url, expected_api_url', (
        ({'api_url': None}, {'api_url': 'http://test_url'}),
        ({'api_url': 'http://different_url'}, {'api_url': 'http://different_url'}),
    ))
    @pytest.mark.parametrize('form_data_username, expected_username', (
        ({'username': None}, {'username': 'testuser'}),
        ({'username': 'different_testuser'}, {'username': 'different_testuser'}),
    ))
    @pytest.mark.parametrize('form_data_password, expected_password', (
        ({'password': None}, {'password': 'supersecret'}),
        ({'password': 'evenmoresupersecret'}, {'password': 'evenmoresupersecret'}),
    ))
    @patch('planning_poker_jira.models.JiraConnection.get_client')
    def test_get_connection(self, mock_get_client, jira_connection_form_class, jira_connection, form_data_api_url,
                            expected_api_url, form_data_username, expected_username, form_data_password,
                            expected_password):
        form_data = dict(**form_data_api_url, **form_data_username, **form_data_password)
        expected_data = dict(**expected_api_url, **expected_username, **expected_password)
        form = jira_connection_form_class(data=form_data, instance=jira_connection)
        form.is_valid()
        # connection = form._get_connection()
        # for attribute, value in expected_data.items():
        #     assert getattr(connection, attribute) == value


class TestExportStoriesForm:
    @patch('planning_poker_jira.models.JiraConnection.get_client')
    def test_get_connection(self, mock_get_client, jira_connection, form_data_username, expected_username,
                            form_data_password, expected_password):
        form_data = dict(**form_data_username, **form_data_password, jira_connection=jira_connection)
        expected_data = dict(**expected_username, **expected_password, api_url=jira_connection.api_url)
        form = ExportStoriesForm(form_data)
        form.is_valid()
        connection = form._get_connection()
        for attribute, value in expected_data.items():
            assert getattr(connection, attribute) == value


class TestImportStoriesForm:

    def test_init(self, jira_connection):
        form = ImportStoriesForm(jira_connection, {})
        assert form._connection == jira_connection

    @patch('planning_poker_jira.models.JiraConnection.get_client')
    def test_get_connection(self, mock_get_client, jira_connection, form_data_username, expected_username,
                            form_data_password, expected_password):
        form_data = dict(**form_data_username, **form_data_password)
        expected_data = dict(**expected_username, **expected_password, api_url=jira_connection.api_url)
        form = ImportStoriesForm(jira_connection, form_data)
        form.is_valid()
        connection = form._get_connection()
        for attribute, value in expected_data.items():
            assert getattr(connection, attribute) == value
