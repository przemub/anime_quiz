from .settings import *  # noqa

DEBUG = False

BUGSNAG = {
    'api_key': '***REMOVED***',
    'project_root': '/usr/src/app',
}
LOGGING["handlers"]["bugsnag"] = {
    'level': 'INFO',
    'class': 'bugsnag.handlers.BugsnagHandler',
}
LOGGING["loggers"]["django"]["handlers"].append("bugsnag")

MIDDLEWARE += ["bugsnag.django.middleware.BugsnagMiddleware"]
