import os
import sys
from time import sleep

import requests
from urllib.parse import quote_plus
from typing import Sequence, Union

POLL_TIMEOUT = 0.1


class FairClient:
    def __init__(self, user_email: str, user_password: str, server_address='https://faircompute.com:8000'):
        self.token = None
        self.server_address = os.path.join(server_address, 'api/v0')
        self.authenticate(user_email, user_password)

    def authenticate(self, user_email: str, user_password: str):
        url = f'{self.server_address}/auth/login'
        json = {"email": user_email, "password": user_password, "version": "V018"}
        resp = requests.post(url, json=json)
        if not resp.ok:
            raise Exception(f"Error! status: {resp.status_code}")
        self.token = resp.json()["token"]

    def _make_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

    def _make_request(self, method, url, **kwargs) -> requests.Response:
        response = requests.request(method, url, headers=self._make_headers(), **kwargs)
        if not response.ok:
            raise Exception(f"Error! status: {response.status_code}")
        return response

    def run(self,
            image: str,
            command: Sequence[str] = tuple(),
            ports: Sequence[tuple[int, int]] = tuple(),
            runtime: str = 'docker',
            detach: bool = False):
        resp = self.put_job(image, command, ports, runtime)
        job_id = resp['job_id']
        bucket_id = resp['bucket_id']

        # upload stdin (empty for now)
        self.put_file_eof(bucket_id, '#stdin')

        # wait for job to get scheduled
        while True:
            job = self.get_job_info(job_id)
            if job['status'] in ('Queued', 'NotResponding'):
                sleep(POLL_TIMEOUT)
            elif job['status'] == 'Processing':
                break
            elif job['status'] == 'Expired':
                raise Exception("Job expired")
            elif job['status'] == 'Completed':
                raise Exception("Job completed before it was scheduled")

        if detach:
            return job
        else:
            # print stdout and stderr
            stdout_data = self.get_file_data(bucket_id, '#stdout')
            stderr_data = self.get_file_data(bucket_id, '#stderr')
            while stdout_data or stderr_data:
                data_received = False
                if stdout_data:
                    try:
                        data = next(stdout_data)
                        if data:
                            sys.stdout.write(data.decode('utf-8'))
                            data_received = True
                    except StopIteration:
                        stdout_data = None
                if stderr_data:
                    try:
                        data = next(stdout_data)
                        if data:
                            sys.stderr.write(data.decode('utf-8'))
                            data_received = True
                    except StopIteration:
                        stderr_data = None

                if not data_received:
                    sleep(POLL_TIMEOUT)

            # wait for job to complete
            while True:
                job = self.get_job_info(job_id)
                if job['status'] in ('Expired', 'Completed'):
                    break
                else:
                    sleep(POLL_TIMEOUT)

            # get result
            return self.get_program_result(job['assignment']['node_id'], job['assignment']['program_id'])

    def put_job(self,
                image: str,
                command: Sequence[str] = tuple(),
                ports: Sequence[tuple[int, int]] = tuple(),
                runtime: str = 'docker'):
        json = {
            'version': 'V018',
            'container_desc': {
                'image': image,
                'runtime': runtime,
                'ports': [[{"port": host_port, "ip": 'null'}, {"port": container_port, "protocol": "Tcp"}] for (host_port, container_port) in ports],
                'command': command,
            },
            'input_files': [],
            'output_files': [],
        }
        return self._make_request('put', url=f"{self.server_address}/jobs", json=json).json()

    def get_job_info(self, job_id):
        return self._make_request('get', url=f"{self.server_address}/jobs/{job_id}/info").json()

    def get_file_data(self, bucket_id: int, file_name: str):
        session = requests.Session()
        with session.get(url=f"{self.server_address}/buckets/{bucket_id}/{quote_plus(file_name)}", headers=self._make_headers(), stream=True) as resp:
            for line in resp.iter_lines():
                yield line

    def put_file_data(self, bucket_id: int, file_name: str, data: Union[str, bytes]):
        return self._make_request('put', url=f"{self.server_address}/buckets/{bucket_id}/{quote_plus(file_name)}", data=data)

    def put_file_eof(self, bucket_id: int, file_name: str):
        return self._make_request('put', url=f"{self.server_address}/buckets/{bucket_id}/{quote_plus(file_name)}/eof")

    def get_program_result(self, node_id: str, program_id: int):
        resp = self._make_request('get', url=f"{self.server_address}/nodes/{node_id}/programs/{program_id}/result").json()
        return resp['result'][-1]['Ok']['exit_code']