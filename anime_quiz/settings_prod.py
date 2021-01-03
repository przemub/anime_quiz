from .settings import *  # noqa

DEBUG = False

BUGSNAG = {
    'api_key': '***REMOVED***',
    'project_root': '/usr/src/app',
}

MIDDLEWARE += ["bugsnag.django.middleware.BugsnagMiddleware"]
