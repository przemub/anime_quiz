FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -d /usr/src/app -s /bin/bash app
USER app
CMD uwsgi --ini uwsgi.cfg

# Expose uwsgi socket and HTTP
EXPOSE 12345 8009

