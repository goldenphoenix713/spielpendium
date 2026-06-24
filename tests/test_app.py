from app import server


def test_healthz_endpoint():
    """Verify that the lightweight health check endpoint returns 200 OK."""
    with server.test_client() as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.data == b"OK"


def test_sw_endpoint():
    """Verify that the Service Worker script is served with correct type."""
    with server.test_client() as client:
        response = client.get("/sw.js")
        assert response.status_code == 200
        assert "application/javascript" in response.content_type
        assert b"spielpendium-cache-v1" in response.data


def test_manifest_endpoint():
    """Verify that the PWA manifest is served with correct type."""
    with server.test_client() as client:
        response = client.get("/manifest.json")
        assert response.status_code == 200
        assert "application/json" in response.content_type
        assert b"Spielpendium" in response.data
