FROM python:3.6.5-slim

# setup virtual env vars
ENV VIRTUAL_ENV=/opt/crypto_app

# create python virtual env
RUN python3 -m venv $VIRTUAL_ENV

# set path
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# update/upgrade
RUN apt-get update && \
    apt-get upgrade -y

# set working dir
WORKDIR ${VIRTUAL_ENV}/crypto-whale-watching-app

# create the assets dir.
RUN mkdir ${VIRTUAL_ENV}/crypto-whale-watching-app/assets

# Add files from assets folder.
COPY ./assets  ${VIRTUAL_ENV}/crypto-whale-watching-app/assets
# Add files to the docker container.
COPY ./app.py ${VIRTUAL_ENV}/crypto-whale-watching-app
COPY ./gdax_book.py ${VIRTUAL_ENV}/crypto-whale-watching-app
COPY ./requirements.txt ${VIRTUAL_ENV}/crypto-whale-watching-app

# install dependencies:
RUN pip install -r requirements.txt

# run the application:
CMD ["python", "app.py"]