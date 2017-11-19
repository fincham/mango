# osquery-controller

## What is this?

An example implementation of a "tls" API server for osquery (in `/api`), and a basic demonstration project (`/osquerycontrol`) showing how it could be used to log the results of arbitrary queries.

## How do I set it up?

If you'd like to use the demo project as-is you'll need to set a few values in settings.py then deploy the application as you usually would for Django (for instance, you might like to use a WSGI server such as `waitress`).

The only requirement is Django 1.11, though it will probably work on earlier Django versions.

You'll need to set a few things in `settings.py`, most importantly the database connection (sqlite is fine), and the `OSQUERY_ENROLL_SECRET`.

Once the application is deployed, create some Log Queries. A good start would be `select * from usb_devices`, but you can play with `osqeuryi` to find other suitable metrics to examine!

### HTTPS in development

`osqueryd` likes to talk to an HTTPS endpoint. The normal `python manage.py runserver` development server in Django doesn't do HTTPS.

The easiest way to resolve this is to use something like `stunnel` to proxy incoming HTTPS connections back to the Django development server.

An example `stunnel` configuration to do this:

    cert = test_server.pem
    key = test_server.key
    foreground = yes
    pid = /tmp/hotplate-hosts-stunnel-dev.pid

    [api]
    accept = localhost:4433
    connect = 8000

`stunnel` can then be launched from the directory where the configuration is kept, e.g. by running `stunnel ./stunnel.conf`

Once `stunnel` is runnning then `osqueryd` may connect to `localhost` on port `4433`.

## What is this for?

Sometimes you just want to experiment with `osqueryd`
