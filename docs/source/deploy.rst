===============
Deploying Voila
===============

The deployment docs are split up in two parts. First there is the
general section, which should always be followed. Then there is a cloud
service provider specific section of which one provider should be chosen.

If you are not sure where to deploy your app, we suggest Heroku. You can test 
deploying and serving your app without having to enter any credit card details,
and with very little prior experience of deployments.

Setup an example project
========================

1. Create a project directory of notebooks you wish to display. For this
   tutorial we will clone voila and treat the notebooks folder as our
   project root.

   .. code:: bash

       git clone git@github.com:QuantStack/voila.git
       cd voila/notebooks/

2. Add a requirements.txt file to the project directory. This file should 
   contain all the Python dependencies your voila app needs to run. For this
   tutorial we will copy the contents of the environment.yml of voila.
   We omit xleaflet and xeus-cling because these require extra work that is
   beyond the scope of this guide.

   .. code:: txt

       bqplot
       ipympl
       ipyvolume
       scipy
       voila

Cloud Service Providers
=======================

Deployment on Heroku
--------------------

Heroku.com is an attractive option if you want to try out deployment for
free. You have limited computing hours, however the app will also
automatically shutdown if it is idle.

The general steps for deployment at Heroku can be found
`here <https://devcenter.heroku.com/articles/getting-started-with-python>`__.
High level instructions, specific to voila can be found below:

1. Follow the steps of the official documentation to install the heroku
   cli and login on your machine.
2. Add a file named runtime.txt to the project directory with the following
   content:

   .. code:: txt

       python-3.7.3

3. Add a file named Procfile to the project directory with the
   following content if you want to show all notebooks:

   ::

       web: voila —-port=$PORT --no-browser

   Or the following if you only want to show one notebook:

   ::

       web: voila —-port=$PORT —-no-browser your_notebook.ipynb

4. Initialize your git repo and commit your code. At minimum you need to commit
   your notebooks, requirements.txt, runtime.txt, and the Procfile.

   .. code:: bash

       git init
       git add <your-files>
       git commit -m "my message"

5. Create an Heroku instance and push the code.

   .. code:: bash

       heroku create
       git push heroku master

6. Open your web app

   .. code:: bash

       heroku open



To resolve issues, it is useful to see the logs of your application. You can do this by running:

   .. code:: bash

       heroku logs --tail



Deployment on Google App Engine
-------------------------------

You can deploy on `Google App
Engine <https://cloud.google.com/appengine/>`__ in a “flexible”
environment. This means that the underlying machine will always run.
This is more expensive than a “standard” environment, which is similar
to Heroku’s free option. However, Google App Engine’s “standard”
environment does not support websockets, which is a requirement for
voila.

The general steps for deployment at Google App Engine can be found
`here <https://cloud.google.com/appengine/docs/flexible/python/quickstart>`__.
High level instructions specific to voila can be found below:

1. Follow the “Before you begin steps” from the official documentation
   to create your account, project and App Engine app.
2. Add an app.yaml file to the project directory with the following content:

   .. code:: yaml

       runtime: python
       env: flex
       runtime_config:
         python_version: 3
       entrypoint: voila --port=$PORT --no-browser 

3. Edit the last line if you want to show only one notebook

   .. code:: yaml

       entrypoint: voila --port=$PORT --no-browser your_notebook.ipynb

4. Deploy your app

   .. code:: bash

       gcloud app deploy

5. Open your app

   .. code:: bash

       gcloud app browse
