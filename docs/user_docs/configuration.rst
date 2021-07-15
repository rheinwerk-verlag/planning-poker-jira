Configuration
=============
The Planning Poker Jira app provides a few options you can set in your settings to customize your experience.

Required Settings
-----------------

- :code:`FIELD_ENCRYPTION_KEYS`: :code:`encrypted_fields` requires this setting to be present in order to encrypt your
  password. See `their docs <https://pypi.org/project/django-searchable-encrypted-fields/>`_ for more information on how
  to setup the encryption keys.

Optional Settings
-----------------

- :code:`JIRA_TIMEOUT` - default :code:`(3.05, 7)`: The timeout between read/connect calls to the Jira backend.

- :code:`JIRA_NUM_RETRIES` - default :code:`0`: The amount of retries for the instantiation of the HTTP session between
  the Jira client and backend.

  .. note::
     You can expect long response times if you set this to anything greater than zero when the session can't be created
     (this includes using an incorrect password).
