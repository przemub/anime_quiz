#      Copyright (c) 2021-26 Przemysław Buczkowski
#
#      This file is part of Anime Quiz.
#
#      Anime Quiz is free software: you can redistribute it and/or modify
#      it under the terms of the GNU Affero General Public License as
#      published by the Free Software Foundation, either version 3 of
#      the License, or (at your option) any later version.
#
#      Anime Quiz is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU Affero General Public License for more details.
#
#      You should have received a copy of the GNU Affero General Public License
#      along with Anime Quiz.  If not, see <https://www.gnu.org/licenses/>.
"""Structured (structlog) logging wiring, shared by the web app and the tasks
worker with Bugsnag support.
"""

import structlog

# Processors shared between structlog-native records and "foreign" stdlib
# records (Django internals, the worker, anything using logging.getLogger()).
_base = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso"),
]

# Applied to records that did NOT originate from structlog before they reach
# the renderer.
foreign_pre_chain = _base + [structlog.stdlib.ExtraAdder()]


def build_logging(json_logs, bugsnag=False):
    """Return a ``logging.config.dictConfig`` dict.

    ``json_logs`` picks the renderer (JSON for prod, a pretty console renderer
    for dev). ``bugsnag`` attaches the ``BugsnagHandler`` to the root logger
    for WARNING+ records.
    """
    renderer = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer()
    )
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    # ConsoleRenderer pretty-prints exc_info itself and warns
                    # if it has already been formatted.
                    *([structlog.processors.format_exc_info] if json_logs else []),
                    renderer,
                ],
                "foreign_pre_chain": foreign_pre_chain,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structured",
            },
        },
        "root": {"handlers": ["console"], "level": "INFO"},
        "loggers": {
            # Full structured traceback on the console for unhandled view
            # exceptions; kept off the root so it isn't also sent to Bugsnag
            # (BugsnagMiddleware already reports the exception once).
            "django.request": {
                "handlers": ["console"],
                "level": "ERROR",
                "propagate": False,
            },
            # django-structlog's request_started / request_finished /
            # request_failed events — likewise console-only.
            "django_structlog.middlewares.request": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    if bugsnag:
        config["handlers"]["bugsnag"] = {
            "level": "WARNING",
            "class": "bugsnag.handlers.BugsnagHandler",
            "extra_fields": {"context": ["task_name", "task_kwargs"]},
        }
        config["root"]["handlers"].append("bugsnag")
        # Bugsnag's own diagnostics must not loop back into the Bugsnag handler.
        config["loggers"]["bugsnag"] = {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        }

    return config


def configure_structlog():
    """Configure structlog so ``structlog.get_logger()`` and django-structlog's
    events flow through the ``ProcessorFormatter`` handlers built above."""
    structlog.configure(
        processors=_base
        + [
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
