.. Copyright (c) 2018, Voilà Contributors
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

   .. code:: text

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
High level instructions, specific to Voilà can be found below:

1. Follow the steps of the official documentation to install the heroku
   cli and login on your machine.
2. Add a file named runtime.txt to the project directory with the following
   content:

   .. code:: text

       python-3.7.3

3. Add a file named Procfile to the project directory with the
   following content if you want to show all notebooks:

   .. code:: text

       web: voila —-port=$PORT --no-browser

   Or the following if you only want to show one notebook:

   .. code:: text

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

Running Voilà on a private server
=================================

Prerequisites
-------------

- A server running Ubuntu 18.04 (or later) with root access.
- Ability to SSH into the server and run commands from the prompt.
- The public IP address of the server.
- A domain name pointing to the IP address of the server.

Steps
-----

1. SSH into the server:

    .. code:: text

        ssh ubuntu@<ip-address>

2. Install nginx:

    .. code:: text

        sudo apt install nginx

3. To check that ``nginx`` is correctly installed:

    .. code:: text

        sudo systemctl status nginx

4. Create the file ``/etc/nginx/sites-enabled/yourdomain.com`` with the following content:

    .. code:: text

        server {
            listen 80;
            server_name yourdomain.com;
            proxy_buffering off;
            location / {
                    proxy_pass http://localhost:8866;
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

                    proxy_http_version 1.1;
                    proxy_set_header Upgrade $http_upgrade;
                    proxy_set_header Connection "upgrade";
                    proxy_read_timeout 86400;
            }

            client_max_body_size 100M;
            error_log /var/log/nginx/error.log;
        }

5. Enable and start the ``nginx`` service:

    .. code:: text

        sudo systemctl enable nginx.service
        sudo systemctl start nginx.service

6. Install pip:

    .. code:: text

        sudo apt update && sudo apt install python3-pip

7. Follow the instructions in `Setup an example project`_, and install the dependencies:

    .. code:: text

        sudo python3 -m pip install -r requirements.txt

8. Create a new systemd service for running Voilà in ``/usr/lib/systemd/system/voila.service``.
The service will ensure Voilà is automatically restarted on startup:

    .. code:: text

        [Unit]
        Description=Voila

        [Service]
        Type=simple
        PIDFile=/run/voila.pid
        ExecStart=voila --no-browser voila/notebooks/basics.ipynb
        User=ubuntu
        WorkingDirectory=/home/ubuntu/
        Restart=always
        RestartSec=10

        [Install]
        WantedBy=multi-user.target

In this example Voilà is started with ``voila --no-browser voila/notebooks/basics.ipynb`` to serve a single notebook.
You can edit the command to change this behavior and the notebooks Voilà is serving.

9. Enable and start the ``voila`` service:

    .. code:: text

        sudo systemctl enable voila.service
        sudo systemctl start voila.service

.. note::
    To check the logs for Voilà:

    .. code:: text

        journalctl -u voila.service


10. Now go to ``yourdomain.com`` to access the Voilà application.

Enable HTTPS with Let's Encrypt
-------------------------------

1. Install ``certbot``:

    .. code:: text

        sudo add-apt-repository ppa:certbot/certbot
        sudo apt update
        sudo apt install python-certbot-nginx

2. Obtain the certificates from Let's Encrypt. The ``--nginx`` flag will edit the nginx configuration automatically:

    .. code:: text

        sudo certbot --nginx -d yourdomain.com

3. ``/etc/nginx/sites-enabled/yourdomain.com`` should now contain a few more entries:

    .. code :: text

        $ cat /etc/nginx/sites-enabled/yourdomain.com

        ...
        listen 443 ssl; # managed by Certbot
        ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem; # managed by Certbot
        ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem; # managed by Certbot
        include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
        ...

4. Visit https://yourdomain.com to access the Voilà applications over HTTPS.

5. To automatically renew the certificates (they expire after 90 days), open the ``crontab`` file:

    .. code :: text

        crontab -e

And add the following line:

    .. code :: text

        0 12 * * * /usr/bin/certbot renew --quiet

For more information, you can also follow `the guide on the nginx blog <https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/>`__.

Sharing Voilà applications with ngrok
=====================================

`ngrok <https://ngrok.com>`__ is a useful tool to expose local servers to the public internet over secure tunnels.
It can be used to share Voilà applications served by a local instance of Voilà.

The main use case for using Voilà with ngrok is to quickly share a notebook as an interactive application without 
having to deploy to external hosting.

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
