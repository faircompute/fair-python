def test_authentication(fair_client):
    # fair_client fixture will raise an exception if authentication fails
    pass


def test_echo_job(fair_client):
    fair_client.run(image='alpine', command=['echo', 'hello world'])
