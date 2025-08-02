from maqro_backend import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_read_main():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {'status' : "healthy"}


if __name__ == "__main__":
    test_read_main()    