def test_authentication(fair_client):
    # fair_client fixture will raise an exception if authentication fails
    pass


def test_echo_job(fair_client):
    assert fair_client.run(image='alpine', command=['echo', 'hello fair compute']) == 0


def test_echo_program(fair_client):
    nodes = fair_client.get_nodes()
    assert fair_client.run(image='alpine', node=nodes[0]['node_id'], command=['echo', 'hello fair compute']) == 0
