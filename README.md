# FairCompute Python Client

FairCompute Python is a Python client for FairCompute API.
It allows to schedule jobs, monitor their status and retrieve results.

## Developing FairCompute Python Client

### Prerequisites

Create virtual environment and install requirements.
```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Testing

By default, testing is done against client running on localhost,
so you need to start the server and at least one compute node locally.
To start the server locally see https://github.com/faircompute/faircompute#running-locally.

Project is using [pytest](https://docs.pytest.org/en/latest/) for testing. To run all tests:
```shell
pytest
```

To run tests against remote server, set `FAIRCOMPUTE_SERVER_URL`, `FAIRCOMPUTE_USER_EMAIL`
and `FAIRCOMPUTE_USER_PASSWORD` environment variables:
```shell
FAIRCOMPUTE_SERVER_URL=http://faircompute:8000 FAIRCOMPUTE_USER_EMAIL=<email> FAIRCOMPUTE_USER_PASSWORD=<password> pytest
```
