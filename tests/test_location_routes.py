import pytest

MUMBAI = {"city": "Mumbai", "lat": 19.07, "lon": 72.88, "country": "India", "country_code": "IN"}


def test_save_list_and_unsave(client):
    assert client.post("/save", json=MUMBAI).get_json() == {"status": "saved"}

    saved = client.get("/saved").get_json()
    assert [(s["city_name"], s["country_code"]) for s in saved] == [("Mumbai", "IN")]

    assert client.post("/unsave", json={"id": saved[0]["id"]}).get_json() == {"status": "removed"}
    assert client.get("/saved").get_json() == []


def test_save_trims_whitespace(client):
    client.post("/save", json={**MUMBAI, "city": "  Mumbai  "})
    assert client.get("/saved").get_json()[0]["city_name"] == "Mumbai"


@pytest.mark.parametrize("duplicate", [
    MUMBAI,
    {**MUMBAI, "city": "mumbai"},             # case-insensitive
    {**MUMBAI, "lat": 19.071, "lon": 72.881},  # same place within rounding
])
def test_duplicate_save_is_rejected(client, duplicate):
    client.post("/save", json=MUMBAI)
    assert client.post("/save", json=duplicate).get_json() == {"status": "already_saved"}
    assert len(client.get("/saved").get_json()) == 1


def test_same_city_name_elsewhere_is_a_new_location(client):
    client.post("/save", json={"city": "Springfield", "lat": 39.80, "lon": -89.64})
    assert client.post("/save", json={"city": "Springfield", "lat": 37.21, "lon": -93.29}).get_json() == {
        "status": "saved"}


@pytest.mark.parametrize("body, field", [
    ({"lat": 10, "lon": 20}, "city"),
    ({"city": "X", "lat": 200, "lon": 20}, "lat"),
    ({"city": "X", "lat": 10, "lon": -181}, "lon"),
    ({"city": "X", "lat": "abc", "lon": 20}, "lat"),
    ({"city": "X" * 101, "lat": 10, "lon": 20}, "city"),
])
def test_save_validation_errors(client, body, field):
    resp = client.post("/save", json=body)
    assert resp.status_code == 400
    error = resp.get_json()["error"]
    assert error["code"] == "validation_error"
    assert field in [d["field"] for d in error["details"]]


@pytest.mark.parametrize("path", ["/save", "/unsave"])
@pytest.mark.parametrize("kwargs", [{}, {"json": [1, 2]}, {"data": "not json", "content_type": "application/json"}])
def test_non_object_body_is_rejected(client, path, kwargs):
    resp = client.post(path, **kwargs)
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "invalid_json"


def test_unsave_unknown_id_is_404(client):
    resp = client.post("/unsave", json={"id": 999})
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "not_found"


def test_unsave_rejects_non_positive_id(client):
    assert client.post("/unsave", json={"id": 0}).status_code == 400


def test_missing_secret_key_generates_temporary_one(tmp_path):
    from app import create_app
    from app.config import Config

    class NoSecret(Config):
        SECRET_KEY = None
        DB_PATH = str(tmp_path / "x.db")

    assert len(create_app(NoSecret).config["SECRET_KEY"]) == 64
