from contextlib import nullcontext as does_not_raise
from unittest.mock import Mock, patch

import pytest
from jira import JIRAError
from requests.exceptions import ConnectionError, RequestException

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
    def test_client(self, form_data, cleaned, expected, jira_connection):
        mock_get_connection = Mock(return_value=jira_connection)

        form = JiraAuthenticationForm(form_data)
        with patch.object(form, '_get_connection', mock_get_connection):
            with patch.object(jira_connection, 'get_client'):
                if cleaned:
                    form.is_valid()
                    form.clean()
                with expected:
                    form.client

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
                jira_authentication_form.clean()

        num_generated_errors = len(jira_authentication_form.errors.get('__all__', []))
        if num_expected_missing_credentials_errors:
            num_expected_errors = num_expected_missing_credentials_errors
            mock_get_client.assert_not_called()
        else:
            num_expected_errors = num_expected_missing_credentials_errors + num_expected_side_effects_errors
        assert num_generated_errors == num_expected_errors

    def test_test_connection(self):
        assert JiraAuthenticationForm().test_connection


class TestJiraConnectionForm:
    def test_init(self):
        class Meta:
            model = JiraConnection
        JiraConnectionForm._meta = Meta
        form = JiraConnectionForm()
        assert form._client is None
        assert form.fields['username'].help_text is None
        assert form.fields['password'].help_text is None

    @patch('planning_poker_jira.models.JiraConnection.get_client')
    def test_get_connection(self, mock_get_client, jira_connection_form_class, jira_connection, form_data,
                            expected_data):
        form = jira_connection_form_class(form_data, instance=jira_connection)
        # We want to test the `_get_connection()` method during the cleaning process, so we need to mock `_post_clean`
        # which would change attributes for `form.instance` which would in turn change the outcome of
        # `_get_connection()`.
        with patch.object(form, '_post_clean'):
            form.is_valid()
        connection = form._get_connection()
        for attribute, value in expected_data.items():
            assert getattr(connection, attribute) == value

    @pytest.mark.parametrize('delete_password_checked', (True, False))
    @pytest.mark.parametrize('password_entered', (True, False))
    def test_clean(self, delete_password_checked, password_entered, form_data, jira_connection_form_class,
                   jira_connection):
        if not password_entered:
            del form_data['password']
        else:
            form_data['password'] = 'custom password'
        form_data['delete_password'] = delete_password_checked
        form = jira_connection_form_class(form_data, instance=jira_connection)

        form.is_valid()

        if password_entered and delete_password_checked:
            assert 'password' in form.errors
        else:
            expected_password = '' if delete_password_checked else form_data.get('password') or jira_connection.password
            assert form.cleaned_data['password'] == expected_password

    @patch('planning_poker_jira.models.JiraConnection.get_client')
    @pytest.mark.parametrize('test_conn_checked', (True, False))
    def test_test_connection(self, mock_get_client, form_data, jira_connection_form_class, test_conn_checked):
        form_data['test_conn'] = test_conn_checked
        form = jira_connection_form_class(form_data)
        form.is_valid()
        assert form.test_connection == test_conn_checked


class TestExportStoriesForm:
    @patch('planning_poker_jira.models.JiraConnection.get_client')
    def test_get_connection(self, mock_get_client, jira_connection, form_data, expected_data):
        form_data = dict(**form_data, jira_connection=jira_connection)
        expected_data['api_url'] = jira_connection.api_url
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
    def test_get_connection(self, mock_get_client, jira_connection, form_data, expected_data):
        form = ImportStoriesForm(jira_connection, form_data)
        expected_data['api_url'] = jira_connection.api_url
        form.is_valid()
        connection = form._get_connection()
        for attribute, value in expected_data.items():
            assert getattr(connection, attribute) == value
