# Fair Compute Python Client

Fair is a Python client for [Fair Compute](https://faircompute.com) API.
It allows to schedule jobs, monitor their status and retrieve results.

### Creating Fair Account

To use FairCompute Python Client you need to have a Fair account.
Please sign up at https://faircompute.com.

### Launching a job

To launch a job, create a `FairClient` instance and call `run` method.

```python
from fair import FairClient

client = FairClient('http://faircompute:8000', '<email>', '<password>')
client.run(image='alpine', command=['echo', 'hello fair compute'])
```

## Developing Fair

This section is for developers of FairCompute Python client library.

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

### Uploading to PyPI

Please follow the instructions at https://packaging.python.org/tutorials/packaging-projects/

```shell
rm -rf dist
python3 -m build
python3 -m twine upload --repository testpypi dist/*
python3 -m twine upload dist/*
```
