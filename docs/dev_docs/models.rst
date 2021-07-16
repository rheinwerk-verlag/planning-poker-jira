Models
======

.. autoclass:: planning_poker_jira.models.JiraConnection
   :members:
   :exclude-members: DoesNotExist, MultipleObjectsReturned

   .. attribute:: label
      :type: django.db.models.CharField

      The label used solely for displaying the Jira Connection to the user.

   .. attribute:: api_url
      :type: django.db.models.CharField

      The API URL used for making requests to the Jira backend.

   .. attribute:: username
      :type: django.db.models.CharField

      The username used for the authentication at the API.

   .. attribute:: password
      :type: encrypted_fields.fields.EncryptedCharField

      The password used for the authentication at the API.

   .. attribute:: story_points_field
      :type: django.db.models.CharField

      The name of the field the Jira backend uses to store the story points.
