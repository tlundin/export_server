FROM python:alpine3.7

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY . /
WORKDIR /


ENV FLASK_APP=flaskAppServer

ENTRYPOINT ["./gunicorn_starter.sh"]
