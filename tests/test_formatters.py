"""Unit tests for formatters (Markdown, CSV, JSON, HTML)."""

import json
from wiki_photos.models import ArticleResult
from wiki_photos.formatters import (
    format_markdown,
    format_csv,
    format_json,
    format_html,
)


def sample_results():
    return [
        ArticleResult(
            ta_title="எஸ். ஆர். ஸ்ரீனிவாச வரதன்",
            en_title="S. R. Srinivasa Varadhan",
            image_name="Srinivasa_Varadhan_Heidelberg.JPG",
            image_url="https://upload.wikimedia.org/.../photo.jpg",
            image_thumbnail_url="https://thumb.wikimedia.org/.../thumb.jpg",
            image_repository="shared",
            wikidata_id="Q370247",
        ),
        ArticleResult(
            ta_title="அனந்து பை",
            en_title="Anant Pai",
            image_name="Uncle_anant_pai.jpg",
            image_repository="local",
        ),
    ]


def test_format_markdown():
    results = sample_results()
    md = format_markdown(results, "பகுப்பு:சோதனை")
    assert "# Missing Photos in Tamil Wikipedia" in md
    assert "எஸ். ஆர். ஸ்ரீனிவாச வரதன்" in md
    assert "S. R. Srinivasa Varadhan" in md
    assert "✅ Yes" in md
    assert "⚠️ Local (en)" in md
    assert "https://commons.wikimedia.org/wiki/File:Srinivasa_Varadhan_Heidelberg.JPG" in md


def test_format_csv():
    results = sample_results()
    csv_text = format_csv(results)
    lines = csv_text.strip().split("\r\n") if "\r\n" in csv_text else csv_text.strip().split("\n")
    assert len(lines) == 3  # Header + 2 rows
    assert "Tamil Title,Tamil URL,English Title" in lines[0]
    assert "எஸ். ஆர். ஸ்ரீனிவாச வரதன்" in lines[1]
    assert "Yes" in lines[1]
    assert "No" in lines[2]


def test_format_json():
    results = sample_results()
    json_text = format_json(results)
    data = json.loads(json_text)
    assert len(data) == 2
    assert data[0]["ta_title"] == "எஸ். ஆர். ஸ்ரீனிவாச வரதன்"
    assert data[0]["is_on_commons"] is True
    assert data[1]["is_on_commons"] is False


def test_format_html():
    results = sample_results()
    html_text = format_html(results, "பகுப்பு:சோதனை")
    assert "<!DOCTYPE html>" in html_text
    assert "Missing Photos in Tamil Wikipedia" in html_text
    assert "எஸ். ஆர். ஸ்ரீனிவாச வரதன்" in html_text
    assert "Anant Pai" in html_text
    assert "Copy Wikitext" in html_text
    assert "Copy Infobox" in html_text
    assert "badge-commons" in html_text
    assert "badge-local" in html_text
