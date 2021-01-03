FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD uwsgi --ini uwsgi.cfg

# Expose uwsgi socket and HTTP
EXPOSE 1234 8000

