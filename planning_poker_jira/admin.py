from typing import Dict, Iterable, List, Union

from django.contrib import messages
from django.contrib.admin import ModelAdmin, helpers, register
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.admin.utils import unquote
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import URLPattern, URLResolver, path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, ngettext_lazy
from jira import JIRAError
from requests.exceptions import ConnectionError, RequestException

from planning_poker.admin import StoryAdmin

from .forms import ExportStoryPointsForm, ImportStoriesForm, JiraConnectionForm
from .models import JiraConnection
from .utils import get_error_text


def export_story_points(modeladmin: ModelAdmin, request: HttpRequest, queryset: QuerySet) -> Union[HttpResponse, None]:
    """Send the story points for each story in the queryset to the selected backend.

    :param modeladmin: The current ModelAdmin.
    :param request: The current HTTP request.
    :param queryset: Containing the set of stories selected by the user.
    :return: A http response which either redirects back to the changelist view on success or renders a template with
             the `ExportStoryPointsForm`.
    """
    submit_button_name = 'export'
    if submit_button_name in request.POST:
        form = ExportStoryPointsForm(request.POST)
        if form.is_valid():
            jira_connection = form.cleaned_data['jira_connection']
            error_message = _('"{story}" could not be exported. {reason}')
            num_exported_stories = 0
            for story in queryset:
                try:
                    jira_story = form.client.issue(id=story.ticket_number, fields='')
                    jira_story.update(fields={jira_connection.story_points_field: story.story_points})
                except (JIRAError, ConnectionError, RequestException) as e:
                    modeladmin.message_user(
                        request,
                        error_message.format(
                            story=story,
                            reason=get_error_text(e, api_url=jira_connection.api_url, connection=jira_connection)
                        ),
                        messages.ERROR
                    )
                else:
                    num_exported_stories += 1
            if num_exported_stories:
                modeladmin.message_user(request, ngettext_lazy(
                    '%d story was successfully exported.',
                    '%d stories were successfully exported.',
                    num_exported_stories,
                ) % num_exported_stories, messages.SUCCESS)
            return None
    else:
        form = ExportStoryPointsForm()
    admin_form = helpers.AdminForm(
        form,
        (
            (None, {
                'fields': ('jira_connection',)
            }),
            (_('Override Options'), {
                'fields': ('username', 'password')
            }),
        ),
        {},
        model_admin=modeladmin
    )
    context = {
        **modeladmin.admin_site.each_context(request),
        'opts': modeladmin.opts,
        'title': _('Export Story Points'),
        'submit_button_name': submit_button_name,
        'action_name': modeladmin.get_action(export_story_points)[1],
        'stories': queryset,
        'form': admin_form,
        'media': modeladmin.media
    }
    return TemplateResponse(request, 'admin/planning_poker/story/export_story_points.html', context)


@register(JiraConnection)
class JiraConnectionAdmin(ModelAdmin):
    form = JiraConnectionForm
    list_display = ('__str__', 'get_import_stories_url')

    def get_urls(self) -> List[Union[URLResolver, URLPattern]]:
        urls = super().get_urls()

        import_stories_path = path('<path:object_id>/import_stories/',
                                   self.admin_site.admin_view(self.import_stories_view),
                                   name='_'.join((self.opts.app_label, self.opts.model_name, 'import_stories')))

        urls.insert(0, import_stories_path)
        return urls

    def get_fields(self, request: HttpRequest, obj: JiraConnection = None) -> Iterable[Union[str, Iterable[str]]]:
        if obj:
            fields = ('label', 'api_url', 'username', ('password', 'delete_password'), 'story_points_field',
                      'test_connection')
        else:
            fields = ('label', 'api_url', 'username', 'password', 'story_points_field', 'test_connection')
        return fields

    def get_import_stories_url(self, obj: JiraConnection) -> str:
        """Create an anchor tag with the link to the object's import stories view.

        :param obj: The jira connection which should be used to determine the url.
        :return: A string containing a html anchor tag where the href attribute points to the import stories view.
        """
        import_stories_url = reverse(admin_urlname(self.opts, 'import_stories'), args=[obj.id])
        return format_html('<a href="{}">{}</a>', import_stories_url, _('Import'))

    get_import_stories_url.short_description = _('Import Stories')

    def import_stories_view(self, request: HttpRequest, object_id: int, extra_context: Dict = None) -> HttpResponse:
        """Render a view where the user can import stories from a jira connection.

        :param request: The current HTTPRequest.
        :param object_id: The id of the jira connection which should be used to import the stories.
        :param extra_context: Additional context which should be added to the view.
        :return: A http response which either redirects back to the changelist view on success or renders a template
                 with the `ImportStoriesForm`.
        """
        obj = self.get_object(request, unquote(object_id))

        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, self.opts, object_id)

        if request.method == 'POST':
            form = ImportStoriesForm(obj, request.POST)
            if form.is_valid():
                try:
                    stories = obj.create_stories(form.cleaned_data['jql_query'],
                                                 form.cleaned_data['poker_session'],
                                                 form.client)
                except (JIRAError, ConnectionError, RequestException) as e:
                    if isinstance(e, JIRAError):
                        field = 'jql_query'
                    else:
                        field = None
                    form.add_error(field, get_error_text(e, api_url=obj.api_url, connection=obj))
                else:
                    num_stories = len(stories)
                    self.message_user(request, ngettext_lazy(
                        '%d story was successfully imported.',
                        '%d stories were successfully imported.',
                        num_stories,
                    ) % num_stories, messages.SUCCESS)
                    return HttpResponseRedirect(reverse(admin_urlname(self.opts, 'changelist')))
        else:
            form = ImportStoriesForm(connection=obj)
        admin_form = helpers.AdminForm(
            form,
            (
                (None, {
                    'fields': ('poker_session', 'jql_query')
                }),
                (_('Override Options'), {
                    'fields': ('username', 'password'),
                }),
            ),
            {},
            model_admin=self
        )
        context = {
            **self.admin_site.each_context(request),
            'opts': self.opts,
            'title': _('Import stories from "{connection}"').format(connection=obj),
            'form': admin_form,
            'object_id': object_id,
        }
        context.update(extra_context or {})
        return TemplateResponse(request, 'admin/planning_poker_jira/jira_connection/import_stories.html', context)


StoryAdmin.add_action(export_story_points, _('Export Story Points to Jira'))
