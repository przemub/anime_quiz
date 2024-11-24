FROM python:3.12 AS build
WORKDIR /usr/src/app

ARG EXTRAS=""

COPY . .
RUN --mount=type=cache,target=/root/.cache/pip pip install --root-user-action ignore build

RUN --mount=type=cache,target=/root/.cache/pip python -m build -w
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --root-user-action ignore dist/anime_quiz-1.0-py3-none-any.whl${EXTRAS}
RUN python manage.py collectstatic --no-input

FROM python:3.12 AS runtime

ARG EXTRAS=""

# Expose uwsgi socket and HTTP
EXPOSE 12345 8009
HEALTHCHECK --start-period=5m \
  CMD curl -f http://localhost:8009/ || exit 1
CMD uwsgi --ini uwsgi.cfg

RUN useradd -d /usr/src/app -s /bin/bash app

WORKDIR /usr/src/app
COPY uwsgi.cfg .
COPY --from=build /usr/src/app/dist dist
COPY --from=build /usr/src/app/static static
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --root-user-action ignore dist/anime_quiz-1.0-py3-none-any.whl${EXTRAS}
RUN rm -r dist

USER app
