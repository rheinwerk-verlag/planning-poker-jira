Planning Poker: Jira Extension
==============================

.. image:: https://codecov.io/gh/rheinwerk-verlag/planning-poker-jira/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/rheinwerk-verlag/planning-poker-jira
   :alt: Code Coverage

.. image:: https://readthedocs.org/projects/planning-poker-jira/badge/?version=stable
   :target: https://planning-poker-jira.readthedocs.io/en/stable/?badge=stable
   :alt: Documentation Status

This application extends the Planning Poker app with the ability to import stories and their description from Jira and
export the estimated amount of story points back to the Jira instance.

This extension also serves as an example on how to add custom behaviour to/extend the functionality of the Planning
Poker app.

Features
--------

- ⬇️ **Import stories** from your backlog and use them to poker.

- ⬆️ **Export story points** back to the Jira backend hassle-free.

- 📋 Easily manage **multiple Jira backends**.

- 🔒 **Securely safe your password** in an encrypted database field.

Quickstart
----------

You'll need an existing system with the Planning Poker app installed. See its
`documentation <https://planning-poker.readthedocs.io/en/stable/>`_ if you haven't already.

#. Install the Planning Poker Jira app. ::

    $ pip install planning-poker-jira

#. Add the app and its dependencies to the list of your installed apps.

   .. code-block:: python

        INSTALLED_APPS = [
            ...
            'planning_poker',
            'encrypted_fields',
            'planning_poker_jira'
        ]

#. Add encryption keys to your settings.
   This is used to encrypt your passwords before they are stored in the database. If you don't already have this
   defined, it's probably easiest to take your ``SECRET_KEY`` and convert it to hex since that should be kept secret
   anyways. See `encrypted fields docs <https://pypi.org/project/django-searchable-encrypted-fields/>`_ for more
   information on this setting.

   .. code-block:: python

        FIELD_ENCRYPTION_KEYS = [SECRET_KEY.encode().hex()[:64]]

   See `configuration <https://planning-poker-jira.readthedocs.io/en/stable/user_docs/configuration.html>`_ for more
   ways to customize the application to fit your needs.

#. Run the migrations. ::

    $ python manage.py migrate

#. You can now start your server. ::

    $ python manage.py runserver 0.0.0.0:8000
