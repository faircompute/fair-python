import tempfile


def test_authentication(fair_client):
    # fair_client fixture will raise an exception if authentication fails
    pass


def test_docker_run(fair_client, capsys):
    assert fair_client.run(image='alpine', command=['echo', 'hello fair compute']) == 0
    captured = capsys.readouterr()
    assert captured.out == "hello fair compute"


def test_docker_run_with_volumes(fair_client, capsys):
    nodes = fair_client.get_nodes()
    with tempfile.NamedTemporaryFile("w") as tmp_file:
        tmp_file.writelines(["temp file created in test"])
        tmp_file.flush()
        assert fair_client.run(image='alpine',
                               node=nodes[0]['node_id'],
                               volumes=[(tmp_file.name, '/app/file.txt')],
                               command=['cat', '/app/file.txt']) == 0
    captured = capsys.readouterr()
    assert captured.out == "temp file created in test"


def test_node_info(fair_client, capsys):
    nodes = fair_client.get_nodes()
    assert nodes[0]['host_address'] == '127.0.0.1'
