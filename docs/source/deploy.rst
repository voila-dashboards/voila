.. Copyright (c) 2018, Voila Contributors
   Copyright (c) 2018, QuantStack
   
   Distributed under the terms of the BSD 3-Clause License.
   
   The full license is in the file LICENSE, distributed with this software.

===============
Deploying Voilà
===============

The deployment docs are split up in two parts. First there is the
general section, which should always be followed. Then there is a cloud
service provider specific section of which one provider should be chosen.

If you are not sure where to deploy your app, we suggest Binder or Heroku. You can test
deploying and serving your app without having to enter any credit card details,
and with very little prior experience of deployments.

Setup an example project
========================

1. Create a project directory of notebooks you wish to display. For this
   tutorial we will clone Voilà and treat the notebooks folder as our
   project root.

   .. code:: bash

       git clone git@github.com:voila-dashboards/voila.git
       cd voila/notebooks/

2. Add a requirements.txt file to the project directory. This file should
   contain all the Python dependencies your Voilà app needs to run. For this
   tutorial we will copy the contents of the environment.yml of Voilà.
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

Deployment on Binder
--------------------

Binder is one of the most accessible ways to deploy Voilà applications.
The service is available at `mybinder.org <https://mybinder.org>`__ and is increasingly
being used for reproducible research, making it an excellent fit for deploying Voilà applications.

1. Make sure the repository is publicly available (on GitHub, Gitlab or as a `gist <https://gist.github.com>`__).

2. Follow `this guide <https://mybinder.readthedocs.io/en/latest/introduction.html#preparing-a-repository-for-binder>`__
   to prepare the repository. For simple deployments, steps listed in `Setup an example project`_ will be sufficient.


.. note::

       Binder also supports ``environment.yml`` files and ``conda`` environments.


3. Go to `mybinder.org <https://mybinder.org>`__ and enter the URL of the repository.

4. In ``Path to a notebook file``, select ``URL`` and use the Voilà endpoint: ``/voila/render/path/to/notebook.ipynb``

5. Click ``Launch``.

6. Binder will trigger a new build if this is the first launch (or if there has been new changes since
   the last build). This might take a few minutes to complete. If an image is already available,
   the server will be able to start within a few seconds.


Customizing Voilà on Binder
***************************

To specify different options (such as the theme and template), create a
``jupyter_config.json`` file at the root of the repository with the following content:

   .. code:: json

       {
         "VoilaConfiguration": {
           "theme": "dark",
           "template": "gridstack"
         }
       }


An example can be found in the
`voila-demo <https://github.com/maartenbreddels/voila-demo>`__ repository.


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
High level instructions specific to Voilà can be found below:

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


Sharing Voilà applications with ngrok
=====================================

`ngrok <https://ngrok.com>`__ is a useful tool to expose local servers to the public internet over secure tunnels.
It can be used to share Voilà applications served by a local instance of Voilà.

The main use case for using Voilà with ngrok is to quickly share a notebook as an interactive application with

.. warning::

   Don't forget to exercise caution before exposing local apps and data to the public over the internet.

   While Voilà does not permit arbitrary code execution, be aware that sensitive information could be exposed,
   depending on the content and the logic of the notebook.

   It's good practice to keep the ngrok tunnel connection short-lived, and limit its use to quick sharing purposes.

Setup ngrok
-----------

To setup ngrok, follow the `Download and setup ngrok <https://ngrok.com/download>`__ guide.

Sharing Voilà applications
--------------------------

1. Start Voilà locally: ``voila --no-browser my_notebook.ipynb``

2. In a new terminal window, start ngrok: ``ngrok http 8866``

3. Copy the link from the ngrok terminal window. The links looks like the following: https://8bb6fded.ngrok.io/

4. Send the link

5. When using the ngrok link, the requests will be forwared to your local instance of Voilà.
