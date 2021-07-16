Forms
=====

This module uses a rather sophisticated forms setup in order to provide the user with many utilities during the
interaction with this extension's functionalities.

.. autoclass:: planning_poker_jira.forms.JiraAuthenticationForm
   :members:
   :private-members:

   .. attribute:: username
      :type: django.forms.CharField

      The username used for the authentication at the API.

   .. attribute:: password
      :type: django.forms.CharField

      The password used for the authentication at the API.

.. autoclass:: planning_poker_jira.forms.JiraConnectionForm
   :members:
   :private-members:

   .. attribute:: test_connection
      :type: django.forms.BooleanField

      Determines whether the connection should be tested.

   .. attribute:: delete_password
      :type: django.forms.BooleanField

      Determines whether the saved password should be deleted.

.. autoclass:: planning_poker_jira.forms.ExportStoryPointsForm
   :members:

   .. attribute:: jira_connection
      :type: django.forms.ModelChoiceField

      This determines the Jira backend you want to export the story points to

.. autoclass:: planning_poker_jira.forms.ImportStoriesForm
   :members:

   .. attribute:: poker_session
      :type: django.forms.ModelChoiceField

      Optional: The poker session to which you want to import the stories


   .. attribute:: jql_query
      :type: django.forms.CharField

      The query which should be used to retrieve the stories from the Jira backend
