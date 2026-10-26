"""Unit tests for WikiPhotoFinder and helper methods."""

from unittest.mock import MagicMock
from wiki_photos.finder import (
    WikiPhotoFinder,
    has_tamil_characters,
    normalize_category_title,
    is_placeholder_image,
)


def test_tamil_character_detection():
    assert has_tamil_characters("பகுப்பு:தமிழ்நாடு") is True
    assert has_tamil_characters("கணிதம்") is True
    assert has_tamil_characters("Category:Tamil writers") is False
    assert has_tamil_characters("English only") is False


def test_normalize_category_title():
    # ta wiki
    assert normalize_category_title("கணிதவியலாளர்கள்", "ta") == "பகுப்பு:கணிதவியலாளர்கள்"
    assert normalize_category_title("பகுப்பு:கணிதவியலாளர்கள்", "ta") == "பகுப்பு:கணிதவியலாளர்கள்"
    assert normalize_category_title("Category:கணிதவியலாளர்கள்", "ta") == "பகுப்பு:கணிதவியலாளர்கள்"

    # en wiki
    assert normalize_category_title("Indian writers", "en") == "Category:Indian writers"
    assert normalize_category_title("Category:Indian writers", "en") == "Category:Indian writers"
    assert normalize_category_title("பகுப்பு:Indian writers", "en") == "Category:Indian writers"


def test_is_placeholder_image():
    assert is_placeholder_image("No_photo_available.svg") is True
    assert is_placeholder_image("Flag_of_India.svg") is True
    assert is_placeholder_image("Replace_this_image_male.png") is True
    assert is_placeholder_image(None) is True
    assert is_placeholder_image("Srinivasa_Varadhan_Heidelberg.JPG") is False
    assert is_placeholder_image("Rajini_with_Helmet.jpg") is False


def test_finder_from_tamil_mock():
    mock_client = MagicMock()

    # 1. Members of category
    mock_client.get_category_members.return_value = [
        {"ns": 0, "title": "கணிதவியலாளர் அ"},
        {"ns": 0, "title": "கணிதவியலாளர் ஆ"},
        {"ns": 14, "title": "பகுப்பு:துணைப்பகுப்பு"},
    ]

    # 2. Pages info on ta wiki
    # Page 'கணிதவியலாளர் அ' has NO image, and has EN link 'Mathematician A'
    # Page 'கணிதவியலாளர் ஆ' HAS image
    mock_client.get_pages_info.side_effect = [
        # Call 1: ta wiki
        {
            "கணிதவியலாளர் அ": {
                "title": "கணிதவியலாளர் அ",
                "has_image": False,
                "wikidata_id": "Q100",
                "langlinks": {"en": "Mathematician A"},
            },
            "கணிதவியலாளர் ஆ": {
                "title": "கணிதவியலாளர் ஆ",
                "has_image": True,
                "image_name": "PhotoB.jpg",
                "wikidata_id": "Q200",
                "langlinks": {"en": "Mathematician B"},
            },
        },
        # Call 2: en wiki for 'Mathematician A'
        {
            "Mathematician A": {
                "title": "Mathematician A",
                "has_image": True,
                "image_name": "Mathematician_A.jpg",
                "image_url": "https://upload.wikimedia.org/.../Mathematician_A.jpg",
                "image_thumbnail_url": "https://thumb.wikimedia.org/.../thumb.jpg",
                "wikidata_id": "Q100",
            }
        },
    ]

    # 3. Image repo info
    mock_client.get_images_info.return_value = {
        "Mathematician_A.jpg": {
            "title": "File:Mathematician A.jpg",
            "repository": "shared",
            "url": "https://upload.wikimedia.org/.../Mathematician_A.jpg",
        }
    }

    finder = WikiPhotoFinder(client=mock_client)
    results = finder.find_missing_photos("பகுப்பு:கணிதவியலாளர்கள்", depth=0)

    assert len(results) == 1
    match = results[0]
    assert match.ta_title == "கணிதவியலாளர் அ"
    assert match.en_title == "Mathematician A"
    assert match.image_name == "Mathematician_A.jpg"
    assert match.is_on_commons is True
    assert match.wikidata_id == "Q100"


def test_finder_from_english_mock():
    mock_client = MagicMock()

    # Members on en wiki
    mock_client.get_category_members.return_value = [
        {"ns": 0, "title": "Editor X"},
    ]

    mock_client.get_pages_info.side_effect = [
        # Call 1: en wiki
        {
            "Editor X": {
                "title": "Editor X",
                "has_image": True,
                "image_name": "Editor_X.png",
                "langlinks": {"ta": "தொகுப்பாளர் எக்ஸ்"},
                "wikidata_id": "Q555",
            }
        },
        # Call 2: ta wiki
        {
            "தொகுப்பாளர் எக்ஸ்": {
                "title": "தொகுப்பாளர் எக்ஸ்",
                "has_image": False,
                "wikidata_id": "Q555",
            }
        },
    ]

    mock_client.get_images_info.return_value = {
        "Editor_X.png": {
            "title": "File:Editor X.png",
            "repository": "shared",
            "url": "https://upload.wikimedia.org/.../Editor_X.png",
        }
    }

    finder = WikiPhotoFinder(client=mock_client)
    results = finder.find_missing_photos("Category:Film Editors", wiki="en")

    assert len(results) == 1
    assert results[0].ta_title == "தொகுப்பாளர் எக்ஸ்"
    assert results[0].en_title == "Editor X"
    assert results[0].is_on_commons is True
