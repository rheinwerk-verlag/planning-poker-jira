from contextlib import nullcontext as does_not_raise
from unittest.mock import Mock, patch

from django.forms.models import modelform_factory
from jira import JIRAError
import pytest
from requests.exceptions import ConnectionError, RequestException

from planning_poker_jira.forms import (ExportStoryPointsForm, ImportStoriesForm, JiraAuthenticationForm,
                                       JiraConnectionForm)
from planning_poker_jira.models import JiraConnection


@pytest.fixture(params=['different_testuser', ''])
def form_data_username(request):
    return {'username': request.param}


@pytest.fixture
def expected_username(form_data_username, jira_connection):
    return {'username': form_data_username.get('username') or jira_connection.username}


@pytest.fixture(params=['evenmoresupersecret', ''])
def form_data_password(request):
    return {'password': request.param}


@pytest.fixture
def expected_password(form_data_password, jira_connection):
    return {'password': form_data_password.get('password') or jira_connection.password}


@pytest.fixture(params=['http://different.url', ''])
def form_data_api_url(request):
    return {'api_url': request.param}


@pytest.fixture
def expected_api_url(form_data_api_url, jira_connection):
    return {'api_url': form_data_api_url.get('api_url') or jira_connection.api_url}


@pytest.fixture
def form_data(form_data_api_url, form_data_username, form_data_password):
    return dict(**form_data_api_url, **form_data_username, **form_data_password)


@pytest.fixture
def expected_data(expected_api_url, expected_username, expected_password):
    return dict(**expected_api_url, **expected_username, **expected_password)


@pytest.fixture
@patch('planning_poker_jira.models.JIRA')
def jira_authentication_form(form_data):
    return JiraAuthenticationForm(form_data)


@pytest.fixture
def jira_connection_form_class():
    return modelform_factory(JiraConnection, form=JiraConnectionForm, fields='__all__')


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

    def test_requires_connection_test(self):
        assert JiraAuthenticationForm()._requires_connection_test()


class TestJiraConnectionForm:
    def test_init(self):
        class Meta:
            model = JiraConnection
        JiraConnectionForm._meta = Meta
        form = JiraConnectionForm()
        assert form._client is None
        assert form.fields['username'].help_text is None

    @patch('planning_poker_jira.models.JiraConnection.get_client', Mock())
    def test_get_connection(self, jira_connection_form_class, jira_connection, form_data,
                            expected_data):
        form = jira_connection_form_class(form_data, instance=jira_connection)
        form.is_valid()
        connection = form._get_connection()

        if not form_data['username']:
            expected_data['username'] = ''
        if not form_data['api_url']:
            expected_data['api_url'] = None
        for attribute, value in expected_data.items():
            assert getattr(connection, attribute) == value

    @pytest.mark.parametrize('delete_password_checked', (True, False))
    @pytest.mark.parametrize('entered_password', ('', 'custom password'))
    def test_clean(self, delete_password_checked, entered_password, form_data, jira_connection_form_class,
                   jira_connection):
        form_data['password'] = entered_password
        form_data['delete_password'] = delete_password_checked
        form = jira_connection_form_class(form_data, instance=jira_connection)

        form.is_valid()

        if entered_password and delete_password_checked:
            assert 'password' in form.errors
        else:
            expected_password = '' if delete_password_checked else entered_password or jira_connection.password
            assert form.cleaned_data['password'] == expected_password

    @patch('planning_poker_jira.models.JiraConnection.get_client', Mock())
    @pytest.mark.parametrize('test_connection_checked', (True, False))
    def test_requires_connection_test(self, form_data, jira_connection_form_class,
                                      test_connection_checked):
        form_data['test_connection'] = test_connection_checked
        form = jira_connection_form_class(form_data)
        form.is_valid()
        assert form._requires_connection_test() == test_connection_checked


class TestExportStoryPointsForm:
    @patch('planning_poker_jira.models.JiraConnection.get_client', Mock())
    def test_get_connection(self, jira_connection, form_data, expected_data):
        form_data = dict(**form_data, jira_connection=jira_connection)
        expected_data['api_url'] = jira_connection.api_url
        form = ExportStoryPointsForm(form_data)
        form.is_valid()
        connection = form._get_connection()
        for attribute, value in expected_data.items():
            assert getattr(connection, attribute) == value


class TestImportStoriesForm:

    def test_init(self, jira_connection):
        form = ImportStoriesForm(jira_connection, {})
        assert form._connection == jira_connection

    @patch('planning_poker_jira.models.JiraConnection.get_client', Mock())
    def test_get_connection(self, jira_connection, form_data, expected_data):
        form = ImportStoriesForm(jira_connection, form_data)
        expected_data['api_url'] = jira_connection.api_url
        form.is_valid()
        connection = form._get_connection()
        for attribute, value in expected_data.items():
            assert getattr(connection, attribute) == value
