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
