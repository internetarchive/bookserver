##################################################################
# OPDS bookserver Docker image
# PLEASE SEE petabox/docker/README.md
##################################################################

FROM ubuntu:xenial
MAINTAINER charles

RUN apt-get -qq update && apt-get install -y \
    python-lxml \
    python-pip

COPY . /bookserver
WORKDIR /bookserver
RUN pip install -r requirements.txt

EXPOSE 80

CMD [ "./bookserver/opds.py" ]
