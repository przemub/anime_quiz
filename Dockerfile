FROM python:3.12

# Expose uwsgi socket and HTTP
EXPOSE 12345 8009
HEALTHCHECK --start-period=5m \
  CMD curl -f http://localhost:8009/ || exit 1
CMD uwsgi --ini uwsgi.cfg

RUN useradd -d /usr/src/app -s /bin/bash app
RUN apt-get update && apt-get install -y libpcre3 libpcre3-dev && rm -r /var/cache/apt/*  # For uWSGI

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input

USER app
