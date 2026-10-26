"""Unit tests for preview module."""

from unittest.mock import MagicMock, patch
from wiki_photos.preview import has_chafa, show_terminal_image


def test_has_chafa():
    # Should be True in this Linux environment where chafa is installed
    assert has_chafa() is True


def test_show_terminal_image_none_format():
    assert show_terminal_image("https://example.com/img.jpg", "UserAgent", image_format="none") is False


def test_show_terminal_image_mock():
    mock_resp = MagicMock(status_code=200, content=b"\xff\xd8\xff...")
    mock_proc = MagicMock(returncode=0, stdout=b"\x1bPq\"1;1...")

    with patch("requests.get", return_value=mock_resp):
        with patch("subprocess.run", return_value=mock_proc):
            res = show_terminal_image(
                "https://upload.wikimedia.org/img.jpg",
                user_agent="WikiPhotoFinder/1.0",
                image_format="sixel",
            )
            assert res is True
