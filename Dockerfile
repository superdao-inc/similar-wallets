FROM google/cloud-sdk:alpine as download
ARG GCP_SERVICE_KEY

WORKDIR /download

COPY ./app/metadata .

RUN echo $GCP_SERVICE_KEY | base64 -d > key_file.json
RUN gcloud auth activate-service-account --key-file=key_file.json

RUN gsutil cp gs://superdao-etl-data/ml/* ./

FROM python:3.8 

WORKDIR /app

COPY --from=download /download /app/app

COPY pyproject.toml poetry.lock /app/

RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# Install necessary dependencies for pandas
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libssl-dev \
#     libpq-dev \
#     libcurl4-gnutls-dev \
#     libproj-dev \
#     libhdf5-serial-dev \
#     libprotobuf-dev \
#     protobuf-compiler \
#     libboost-all-dev


COPY ./app /app/app

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
