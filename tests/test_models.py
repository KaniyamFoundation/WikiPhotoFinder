"""Unit tests for ArticleResult model."""

from wiki_photos.models import ArticleResult


def test_article_result_properties():
    res = ArticleResult(
        ta_title="எஸ். ஆர். ஸ்ரீனிவாச வரதன்",
        en_title="S. R. Srinivasa Varadhan",
        image_name="File:Srinivasa_Varadhan_Heidelberg.JPG",
        image_url="https://upload.wikimedia.org/wikipedia/commons/3/32/Srinivasa_Varadhan_Heidelberg.JPG",
        image_thumbnail_url="https://thumb.wikimedia.org/.../60px-photo.jpg",
        image_repository="shared",
        wikidata_id="Q370247",
        source_category="பகுப்பு:இந்தியக் கணிதவியலாளர்கள்",
    )

    assert res.clean_image_name == "Srinivasa Varadhan Heidelberg.JPG"
    assert res.clean_image_filename == "Srinivasa_Varadhan_Heidelberg.JPG"
    assert res.is_on_commons is True
    assert "https://ta.wikipedia.org/wiki/" in res.ta_url
    assert "https://en.wikipedia.org/wiki/S._R._Srinivasa_Varadhan" in res.en_url
    assert res.file_page_url == "https://commons.wikimedia.org/wiki/File:Srinivasa_Varadhan_Heidelberg.JPG"
    assert res.wikidata_url == "https://www.wikidata.org/wiki/Q370247"
    assert res.wikitext_snippet == "[[படிமம்:Srinivasa Varadhan Heidelberg.JPG|mini|எஸ். ஆர். ஸ்ரீனிவாச வரதன்]]"
    assert res.infobox_snippet == "| படம் = Srinivasa Varadhan Heidelberg.JPG"


def test_article_result_local_repository():
    res = ArticleResult(
        ta_title="அனந்து பை",
        en_title="Anant Pai",
        image_name="Uncle_anant_pai.jpg",
        image_repository="local",
    )

    assert res.is_on_commons is False
    assert res.file_page_url == "https://en.wikipedia.org/wiki/File:Uncle_anant_pai.jpg"


def test_to_dict():
    res = ArticleResult(
        ta_title="கு. அண்ணாமலை",
        en_title="K. Annamalai (BJP politician)",
        image_name="File:K._Annamalai.jpg",
        image_repository="shared",
    )
    d = res.to_dict()
    assert d["ta_title"] == "கு. அண்ணாமலை"
    assert d["en_title"] == "K. Annamalai (BJP politician)"
    assert d["is_on_commons"] is True
    assert "wikitext_snippet" in d
    assert "infobox_snippet" in d
