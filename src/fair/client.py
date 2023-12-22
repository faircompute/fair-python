import random
import os
import sys
from time import sleep
from typing import Sequence, Union, Optional
from urllib.parse import quote_plus

import requests

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
            volumes: Sequence[tuple[str, str]] = tuple(),
            runtime: str = 'docker',
            network: str = 'bridge',
            node: Optional[str] = None,
            detach: bool = False):
        if node is None or node == 'any':
            nodes = self.get_nodes()
            if len(nodes) == 0:
                raise Exception(f"No nodes found")
            node = random.choice(nodes)['node_id']
        return self._run_program(node, image, command, ports=ports, runtime=runtime,
                                 network=network, volumes=volumes, detach=detach)

    def _run_program(self,
                     node_id: str,
                     image: str,
                     command: Sequence[str] = tuple(),
                     ports: Sequence[tuple[int, int]] = tuple(),
                     volumes: Sequence[tuple[str, str]] = tuple(),
                     runtime: str = 'docker',
                     network: str = 'bridge',
                     detach: bool = False):
        commands = [
            {
                'type': 'Create',
                'container_desc': {
                    'image': image,
                    'runtime': runtime,
                    'ports': [[{"port": host_port, "ip": 'null'}, {"port": container_port, "protocol": "Tcp"}] for (host_port, container_port) in ports],
                    'command': command,
                    'host_config': {
                        'network_mode': network
                    }
                },
            },
            *[
                {
                    'type': 'CopyInto',
                    'container_id': '$0',
                    'bucket_id': (1 << 64) - 1,
                    'remote_key': remote_path,  # we use remote_path as key to reference the file in the bucket
                                                # key is an arbitrary string
                    'local_path': remote_path
                }
                for _, remote_path in volumes
            ],
            {
                'type': 'Start',
                'container_id': '$0',
            },
        ]
        if not detach:
            commands.append({
                'type': 'Wait',
                'container_id': '$0',
            })

        resp = self.put_program(node_id, commands)
        program_id = resp['program_id']
        bucket_id = resp['bucket_id']

        for local_path, remote_path in volumes:
            with open(local_path) as f:
                data = f.read()
                self.put_file_data(bucket_id=bucket_id, file_name=remote_path, data=data)
                self.put_file_eof(bucket_id=bucket_id, file_name=remote_path)

        # upload stdin (empty for now)
        self.put_file_eof(bucket_id, '#stdin')

        # wait for program to get scheduled
        while True:
            program_info = self.get_program_info(node_id, program_id)
            if program_info['status'] in ('Queued', 'NotResponding'):
                sleep(POLL_TIMEOUT)
            elif program_info['status'] in ('Processing', 'Completed'):
                break
            else:
                raise RuntimeError("Unexpected program status: {}".format(program_info['status']))

        if detach:
            return program_info
        else:
            self._poll_output(bucket_id)

            # wait for job to complete
            while True:
                job = self.get_program_info(node_id, program_id)
                if job['status'] == 'Completed':
                    break
                else:
                    sleep(POLL_TIMEOUT)

            # get result
            return self.get_program_result(node_id, program_id)

    def _poll_output(self, bucket_id: int):
        # print stdout and stderr
        stdout_data = self.get_file_data(bucket_id, '#stdout')
        stderr_data = self.get_file_data(bucket_id, '#stderr')
        while stdout_data is not None or stderr_data is not None:
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
                    data = next(stderr_data)
                    if data:
                        sys.stderr.write(data.decode('utf-8'))
                        data_received = True
                except StopIteration:
                    stderr_data = None

            if not data_received:
                sleep(POLL_TIMEOUT)

    def get_nodes(self):
        return self._make_request('get', url=f"{self.server_address}/nodes").json()['nodes']

    def put_program(self,
                    node_id: str,
                    commands: Sequence[dict]):
        json = {
            'version': 'V018',
            'commands': commands,
        }
        return self._make_request('put', url=f"{self.server_address}/nodes/{node_id}/programs", json=json).json()

    def get_program_info(self, node_id, program_id):
        return self._make_request('get', url=f"{self.server_address}/nodes/{node_id}/programs/{program_id}/info").json()

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
