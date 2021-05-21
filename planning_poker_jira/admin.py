from datetime import datetime
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from jira import JIRAError

from planning_poker.admin import StoryAdmin
from planning_poker.models import PokerSession

from .models import JiraConnection


def send_points_to_backend(modeladmin, request, queryset):
    """Send the story points for each story in the queryset to the backend.

    :param modeladmin: The current ModelAdmin.
    :param request: The current HTTP request.
    :param queryset: Containing the set of stories selected by the user.
    :return:
    """
    for story in queryset.filter(jirastory__isnull=False):
        pass


class JiraConnectionForm(forms.ModelForm):
    password1 = forms.CharField(label=_('Password'), required=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Repeat Password'), required=False, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 != password2:
            error_message = _("The passwords didn't match")
            self.add_error('password1', error_message)
            self.add_error('password2', error_message)
        return cleaned_data

    def save(self, commit=True):
        self.instance.password = self.cleaned_data['password1']
        return super().save(commit)


@admin.register(JiraConnection)
class JiraConnectionAdmin(admin.ModelAdmin):
    form = JiraConnectionForm
    fields = ('label', 'api_url', 'username', 'password1', 'password2', 'story_points_field')


StoryAdmin.actions.append(send_points_to_backend)
