from functools import update_wrapper

from django import forms
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import unquote
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, ngettext_lazy
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


class ImportStoriesForm(forms.Form):
    poker_session = forms.ModelChoiceField(
        label=_('Poker Session'),
        help_text=_('The poker session to which the imported stories should be added'),
        queryset=PokerSession.objects.all(),
        required=False
    )
    jql_query = forms.CharField(label=_('JQL Query'), required=True)
    username = forms.CharField(label=_('Username'),
                               help_text=_('You can use this to override the username saved in the database'),
                               required=False)
    password1 = forms.CharField(label=_('Password'),
                                help_text=_('You can use this to override the username password in the database'),
                                required=False,
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Confirm Password'), required=False, widget=forms.PasswordInput)

    def clean(self) -> dict:
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 != password2:
            error_message = _("The passwords didn't match")
            self.add_error('password1', error_message)
            self.add_error('password2', error_message)
        return cleaned_data


@admin.register(JiraConnection)
class JiraConnectionAdmin(admin.ModelAdmin):
    form = JiraConnectionForm
    fields = ('label', 'api_url', 'username', 'password1', 'password2', 'story_points_field')
    list_display = ('__str__', 'get_import_stories_url')

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        import_stories_path = path('<path:object_id>/import_stories', wrap(self.import_stories_view),
                                   name='%s_%s_import_stories' % info)

        urls.insert(-2, import_stories_path)
        return urls

    def get_import_stories_url(self, obj):
        model = type(obj)
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        import_stories_url = reverse(f'admin:{app_label}_{model_name}_import_stories', args=[obj.id])
        return format_html('<a href="{}">{}</a>', import_stories_url, _('Import'))
    get_import_stories_url.short_description = _('Import Stories')

    def import_stories_view(self, request, object_id, extra_context=None) -> HttpResponse:
        obj = self.get_object(request, unquote(object_id))

        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, self.model._meta, object_id)

        if request.method == 'POST':
            form = ImportStoriesForm(request.POST)
            if form.is_valid():
                try:
                    stories = obj.create_stories(form.cleaned_data['jql_query'],
                                                 form.cleaned_data['poker_session'],
                                                 form.cleaned_data['username'] or obj.username,
                                                 form.cleaned_data['password1'] or obj.password)
                except JIRAError as e:
                    error_text = e.text if e.status_code == 400 else e.status_code
                    form.add_error('jql_query', error_text)
                else:
                    num_stories = len(stories)
                    self.message_user(request, ngettext_lazy(
                        '%d story was successfully imported.',
                        '%d stories were successfully imported.',
                        num_stories,
                    ) % num_stories, messages.SUCCESS)
                    redirect_url = f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist'
                    return HttpResponseRedirect(reverse(redirect_url))
        else:
            form = ImportStoriesForm()
        admin_form = helpers.AdminForm(
            form,
            (
                (None, {
                    'fields': ('poker_session', 'jql_query')
                }),
                ('Override Options', {
                    'fields': ('username', 'password1', 'password2'),
                }),
            ),
            {},
            model_admin=self
        )
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': _(f'Import stories from {obj}'),
            'form': admin_form,
            'object_id': object_id,
        }
        context.update(extra_context or {})
        return TemplateResponse(request, 'admin/planning_poker_jira/jira_connection/import_stories_form.html', context)


StoryAdmin.actions.append(send_points_to_backend)
