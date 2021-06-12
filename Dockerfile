FROM python:3.6.5-slim

# setup virtual env vars
ENV VIRTUAL_ENV=/opt/crypto_app

# create python virtual env
RUN python3 -m venv $VIRTUAL_ENV

# set path
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# update/upgrade and install git
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    git-all

# make active dir for git install
WORKDIR $VIRTUAL_ENV

# Dev stuff
RUN mkdir ${VIRTUAL_ENV}/crypto-whale-watching-app

# set new working dir to 
WORKDIR ${VIRTUAL_ENV}/crypto-whale-watching-app


# Add files from the repo to the docker container.
ADD . ${VIRTUAL_ENV}/crypto-whale-watching-app/

# install dependencies:
RUN pip install -r requirements.txt

# run the application:
CMD ["python", "app.py"]