"""Unit tests for MediaWikiClient."""

from unittest.mock import MagicMock, patch
from wiki_photos.api import MediaWikiClient


def test_get_api_url():
    assert MediaWikiClient.get_api_url("ta") == "https://ta.wikipedia.org/w/api.php"
    assert MediaWikiClient.get_api_url("en") == "https://en.wikipedia.org/w/api.php"
    assert MediaWikiClient.get_api_url("TA ") == "https://ta.wikipedia.org/w/api.php"


def test_get_category_members_pagination():
    client = MediaWikiClient(request_delay=0)
    mock_responses = [
        # Page 1
        MagicMock(
            json=lambda: {
                "batchcomplete": "",
                "continue": {"cmcontinue": "continue_token", "continue": "-||"},
                "query": {
                    "categorymembers": [
                        {"pageid": 1, "ns": 0, "title": "Article 1"},
                        {"pageid": 2, "ns": 0, "title": "Article 2"},
                    ]
                },
            },
            raise_for_status=lambda: None,
        ),
        # Page 2
        MagicMock(
            json=lambda: {
                "batchcomplete": "",
                "query": {
                    "categorymembers": [
                        {"pageid": 3, "ns": 0, "title": "Article 3"},
                    ]
                },
            },
            raise_for_status=lambda: None,
        ),
    ]

    with patch.object(client.session, "post", side_effect=mock_responses):
        members = client.get_category_members("ta", "பகுப்பு:சோதனை")
        assert len(members) == 3
        assert [m["title"] for m in members] == ["Article 1", "Article 2", "Article 3"]


def test_get_pages_info():
    client = MediaWikiClient(request_delay=0)
    mock_resp = MagicMock(
        json=lambda: {
            "query": {
                "normalized": [{"from": "article 1", "to": "Article 1"}],
                "pages": {
                    "101": {
                        "pageid": 101,
                        "title": "Article 1",
                        "pageimage": "Photo1.jpg",
                        "thumbnail": {"source": "https://thumb/photo1.jpg"},
                        "original": {"source": "https://orig/photo1.jpg"},
                        "pageprops": {"wikibase_item": "Q101"},
                        "langlinks": [{"lang": "en", "*": "Article 1 EN"}],
                    }
                },
            }
        },
        raise_for_status=lambda: None,
    )

    with patch.object(client.session, "post", return_value=mock_resp):
        info = client.get_pages_info("ta", ["article 1"], target_lang="en")
        assert "Article 1" in info
        # Should also be accessible via queried original title
        assert "article 1" in info
        res = info["Article 1"]
        assert res["has_image"] is True
        assert res["image_name"] == "Photo1.jpg"
        assert res["wikidata_id"] == "Q101"
        assert res["langlinks"]["en"] == "Article 1 EN"


def test_get_images_info():
    client = MediaWikiClient(request_delay=0)
    mock_resp = MagicMock(
        json=lambda: {
            "query": {
                "pages": {
                    "-1": {
                        "title": "File:Photo.jpg",
                        "imagerepository": "shared",
                        "imageinfo": [
                            {
                                "url": "https://commons/photo.jpg",
                                "descriptionurl": "https://commons/wiki/File:Photo.jpg",
                            }
                        ],
                    }
                }
            }
        },
        raise_for_status=lambda: None,
    )

    with patch.object(client.session, "post", return_value=mock_resp):
        info = client.get_images_info("en", ["Photo.jpg"])
        assert "Photo.jpg" in info
        assert info["Photo.jpg"]["repository"] == "shared"
        assert info["Photo.jpg"]["url"] == "https://commons/photo.jpg"


def test_maxlag_retry():
    client = MediaWikiClient(request_delay=0, maxlag=5, max_retries=3)

    lag_resp = MagicMock(
        status_code=200,
        headers={"Retry-After": "1"},
        json=lambda: {"error": {"code": "maxlag", "info": "Waiting for db"}},
        raise_for_status=lambda: None,
    )
    success_resp = MagicMock(
        status_code=200,
        headers={},
        json=lambda: {"query": {"pages": {}}},
        raise_for_status=lambda: None,
    )

    with patch("time.sleep") as mock_sleep:
        with patch.object(client.session, "post", side_effect=[lag_resp, success_resp]):
            data = client._post("https://ta.wikipedia.org/w/api.php", {"action": "query"})
            assert "query" in data
            # Verify sleep was called for the Retry-After interval
            mock_sleep.assert_called_with(1)


def test_rate_limit_429_retry():
    client = MediaWikiClient(request_delay=0, maxlag=5, max_retries=3)

    resp_429 = MagicMock(
        status_code=429,
        headers={"Retry-After": "2"},
        raise_for_status=lambda: None,
    )
    resp_200 = MagicMock(
        status_code=200,
        headers={},
        json=lambda: {"batchcomplete": ""},
        raise_for_status=lambda: None,
    )

    with patch("time.sleep") as mock_sleep:
        with patch.object(client.session, "post", side_effect=[resp_429, resp_200]):
            data = client._post("https://ta.wikipedia.org/w/api.php", {"action": "query"})
            assert "batchcomplete" in data
            mock_sleep.assert_called_with(2)
