Development Setup
=================

If you want to help the development of this application and need a working setup, you can follow the steps below:

#. Clone the repository and move into the directory. ::

   $ git clone -b development https://github.com/rheinwerk-verlag/planning-poker-jira.git
   $ cd planning-poker-jira

#. Install the Python requirements. ::

   $ pip install -r requirements/dev.txt

#. Run the Django migrations. ::

   $ python manage.py migrate

#. It is useful to have a superuser while developing. ::

   $ python manage.py createsuperuser

#. Finally, start your development server. ::

   $ python manage.py runserver 0.0.0.0:8000

.. note::

   There is an example project in this repository which has configured all the necessary settings for a minimal working
   setup. Feel free to configure the project to your liking while developing. See the
   :ref:`user_docs/configuration:Configuration` section for more ways you can configure this setup.
