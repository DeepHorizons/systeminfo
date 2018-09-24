FROM deephorizons/singularity:2.6.0

# For Click
# http://click.pocoo.org/python3/
ENV LC_LANG=C.UTF-8
ENV LANG=C.UTF-8
# Install the project and its dependencies

RUN apt-get install -y \
    python3 \
    python3-pip && \
    pip3 install pipenv gunicorn

RUN mkdir -p /opt/systeminfo

ADD . /opt/systeminfo

CMD cd /opt/systeminfo/web && pipenv install && pipenv run python app.py
