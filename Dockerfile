FROM pypy:3

RUN mkdir -p /data
RUN pip install pipenv gunicorn

ADD . /data

RUN cd /data/web && pypy3 app.py
