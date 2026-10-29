"""Unit tests for TamilWikiUpdater."""

from unittest.mock import MagicMock, patch
from wiki_photos.updater import TamilWikiUpdater


def test_clean_image_filename():
    assert TamilWikiUpdater.clean_image_filename("File:Ramchundra.jpg") == "Ramchundra.jpg"
    assert TamilWikiUpdater.clean_image_filename("படிமம்:Photo.png") == "Photo.png"
    assert TamilWikiUpdater.clean_image_filename("கோப்பு:Test.jpg") == "Test.jpg"


def test_apply_image_to_wikitext_no_infobox():
    content = "'''ராமச்சந்திரா''' கணிதவியலாளர்."
    updated = TamilWikiUpdater.apply_image_to_wikitext(content, "ராமச்சந்திரா", "Ramchundra.jpg")
    assert updated.startswith("[[படிமம்:Ramchundra.jpg|thumb|ராமச்சந்திரா]]\n\n")


def test_apply_image_to_wikitext_infobox_insertion():
    content = "{{Infobox person\n| name = Test\n}}\nContent"
    updated = TamilWikiUpdater.apply_image_to_wikitext(content, "Test", "Test.jpg")
    assert "{{Infobox person\n| image = Test.jpg\n| name = Test" in updated


def test_apply_image_to_wikitext_fill_empty_param():
    content = "{{Infobox person\n| name = Test\n| image = \n| birth = 1950\n}}"
    updated = TamilWikiUpdater.apply_image_to_wikitext(content, "Test", "Test.jpg")
    assert "| image = Test.jpg\n" in updated


def test_updater_login_mock():
    updater = TamilWikiUpdater()

    mock_login_token_resp = MagicMock(
        json=lambda: {"query": {"tokens": {"logintoken": "tok123"}}},
        raise_for_status=lambda: None,
    )
    mock_login_resp = MagicMock(
        json=lambda: {"login": {"result": "Success", "lgusername": "MyUser@Bot"}},
        raise_for_status=lambda: None,
    )
    mock_csrf_resp = MagicMock(
        json=lambda: {"query": {"tokens": {"csrftoken": "csrf123+\\"}}},
        raise_for_status=lambda: None,
    )

    with patch.object(updater.session, "get", side_effect=[mock_login_token_resp, mock_csrf_resp]):
        with patch.object(updater.session, "post", return_value=mock_login_resp):
            success = updater.login("MyUser@Bot", "secret_pass")
            assert success is True
            assert updater.logged_in_user == "MyUser@Bot"
            assert updater.csrf_token == "csrf123+\\"


def test_updater_edit_page_mock():
    updater = TamilWikiUpdater()
    updater.csrf_token = "valid_csrf"

    mock_edit_resp = MagicMock(
        json=lambda: {"edit": {"result": "Success", "pageid": 1234, "title": "Test"}},
        raise_for_status=lambda: None,
    )

    with patch.object(updater.session, "post", return_value=mock_edit_resp):
        res = updater.edit_page("Test", "new text", "Summary")
        assert res.get("result") == "Success"
        assert res.get("pageid") == 1234


def test_updater_edit_page_ratelimit_retry():
    updater = TamilWikiUpdater()
    updater.csrf_token = "valid_csrf"

    mock_rate_limit_resp = MagicMock(
        json=lambda: {"error": {"code": "ratelimited", "info": "You've exceeded your rate limit."}},
        headers={"Retry-After": "1"},
        raise_for_status=lambda: None,
    )
    mock_success_resp = MagicMock(
        json=lambda: {"edit": {"result": "Success", "pageid": 5678, "title": "Test"}},
        raise_for_status=lambda: None,
    )

    with patch("time.sleep") as mock_sleep:
        with patch.object(updater.session, "post", side_effect=[mock_rate_limit_resp, mock_success_resp]):
            res = updater.edit_page("Test", "new text", "Summary")
            assert res.get("result") == "Success"
            assert res.get("pageid") == 5678
            mock_sleep.assert_any_call(1)
