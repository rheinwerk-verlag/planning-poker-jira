from datetime import datetime
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from planning_poker.models import PokerSession

from .models import JiraConnection


class JiraConnectionForm(forms.ModelForm):
    poker_session = forms.ModelChoiceField(PokerSession.objects.filter(poker_date__gte=datetime.now()), required=False)
    jql_query = forms.CharField(required=False)
    password = forms.CharField(required=False, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        poker_session = cleaned_data.get('poker_session')
        jql_query = cleaned_data.get('jql_query')
        password = cleaned_data.get('password')

        if jql_query and not poker_session:
            self.add_error('poker_session', _('Choose a Poker Session to which the stories should be added'))
        if jql_query and not password:
            self.add_error('password', _('Enter the correct password for the user {user}'.format(
                user=cleaned_data.get('username'))))
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit)
        jql_query = self.cleaned_data['jql_query']
        poker_session = self.cleaned_data['poker_session']
        password = self.cleaned_data['password']
        if jql_query and poker_session:
            self.instance.create_stories(jql_query, poker_session, password)
        return instance


@admin.register(JiraConnection)
class JiraConnectionAdmin(admin.ModelAdmin):

    def get_fieldsets(self, request, obj=None):
        if obj is not None:
            return (
                (
                    _('Import Stories'), {
                        'fields': ('poker_session', 'jql_query', 'password')
                    }
                ),
                (
                    None, {
                        'fields': ('api_url', 'username', 'story_points_field')
                    }
                )
            )
        else:
            return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is not None:
            kwargs['form'] = JiraConnectionForm
        return super().get_form(request, obj, **kwargs)
