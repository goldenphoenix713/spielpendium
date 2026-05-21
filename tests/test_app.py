from app import server


def test_healthz_endpoint():
    """Verify that the lightweight health check endpoint returns 200 OK."""
    with server.test_client() as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.data == b"OK"
