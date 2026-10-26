"""Unit tests for WikidataClient."""

from unittest.mock import MagicMock, patch
from wiki_photos.wikidata import WikidataClient


def test_get_p18_images():
    client = WikidataClient(request_delay=0)

    mock_resp = {
        "entities": {
            "Q100": {
                "claims": {
                    "P18": [
                        {
                            "mainsnak": {
                                "datavalue": {"value": "Photo100.jpg"}
                            }
                        }
                    ]
                }
            },
            "Q200": {
                "claims": {}
            },
        }
    }

    with patch.object(client.mw_client, "_post", return_value=mock_resp):
        res = client.get_p18_images(["Q100", "Q200"])
        assert res["Q100"] == "Photo100.jpg"
        assert res["Q200"] is None


def test_has_p18_image():
    client = WikidataClient(request_delay=0)
    with patch.object(client, "get_p18_images", return_value={"Q123": "Test.jpg"}):
        has_img, name = client.has_p18_image("Q123")
        assert has_img is True
        assert name == "Test.jpg"

    with patch.object(client, "get_p18_images", return_value={"Q456": None}):
        has_img, name = client.has_p18_image("Q456")
        assert has_img is False
        assert name is None


def test_add_p18_image_mock():
    client = WikidataClient(request_delay=0)
    client.csrf_token = "valid_csrf_token"

    mock_post_resp = {
        "claim": {"id": "Q123$guid"},
        "success": 1,
    }

    with patch.object(client.mw_client, "_post", return_value=mock_post_resp) as mock_post:
        res = client.add_p18_image("Q123", "File:My_Photo.jpg", summary="Add P18")
        assert res["success"] == 1
        args, kwargs = mock_post.call_args
        payload = kwargs if kwargs else args[1]
        assert payload["action"] == "wbcreateclaim"
        assert payload["entity"] == "Q123"
        assert payload["property"] == "P18"
        assert payload["value"] == '"My Photo.jpg"'
