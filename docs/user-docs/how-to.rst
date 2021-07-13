How to Use the Extension
========================

The Planning Poker Jira extension provides a new model called Jira Connection. You can use this model to save all the
necessary data to import stories and their description from a jira backend. A Jira Connection consists of multiple
fields:

+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Field Name         | Description                                                                                                                                                  |
+====================+==============================================================================================================================================================+
| Label              | A human readable label for the connection. You can choose this to be whatever you want to help you differentiate different Jira Connections from one another |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| API URL            | The API URL of the jira backend you want to import from / export to                                                                                          |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Username           | The username used for the authentication at the API                                                                                                          |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Password           | The password used for the authentication at the API                                                                                                          |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Story Points Field | The name of the field the jira backend uses to store the story points                                                                                        |
+--------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+

.. note::

   The username and password can be left blank if you don't wan to to save them in the database (the password would be
   saved in an encrypted field). But doing so will cause you re-enter your credentials every time you want to import /
   export stories.

Importing Stories
~~~~~~~~~~~~~~~~~

Once you have created a Jira Connection, you can start importing stories from there. Navigate to the Jira Connection
admin page. There you'll see all your saved connections with an import stories link next to them. You'll be redirected
to a page where you are presented with a form which allows you to import stories if you click on said link.

+---------------+----------------------------------------------------------------------------------------------------------+
| Field Name    | Description                                                                                              |
+===============+==========================================================================================================+
| Poker Session | Optional: The poker session to which you want to import the stories                                      |
+---------------+----------------------------------------------------------------------------------------------------------+
| JQL Query     | The query which should be used to retrieve the stories from the jira backend                             |
+---------------+----------------------------------------------------------------------------------------------------------+
| Username      | Use this if you didn't save a username in the Jira Connection or override the username from the database |
+---------------+----------------------------------------------------------------------------------------------------------+
| Password      | Use this if you didn't save a password in the Jira Connection or override the password from the database |
+---------------+----------------------------------------------------------------------------------------------------------+

Exporting Story Points
~~~~~~~~~~~~~~~~~~~~~~

Exporting story points is as simple as import stories. Go to the Story admin page and select all the stories from which
you want to export the story points. Then choose the "Export Story Points to Jira" action and click the "Go" button.
You'll then be prompted with a form which allows you to export the story points.

+-----------------+----------------------------------------------------------------------------------------------------------+
| Field Name      | Description                                                                                              |
+=================+==========================================================================================================+
| Jira Connection | This determines the jira backend you want to export the story points to                                  |
+-----------------+----------------------------------------------------------------------------------------------------------+
| Username        | Use this if you didn't save a username in the Jira Connection or override the username from the database |
+-----------------+----------------------------------------------------------------------------------------------------------+
| Password        | Use this if you didn't save a password in the Jira Connection or override the password from the database |
+-----------------+----------------------------------------------------------------------------------------------------------+
