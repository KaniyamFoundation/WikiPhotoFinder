"""Integration test verifying end-to-end against live MediaWiki APIs."""

import pytest
from wiki_photos.finder import WikiPhotoFinder


@pytest.mark.integration
def test_live_search_writers():
    finder = WikiPhotoFinder()
    results = finder.find_missing_photos(
        category="பகுப்பு:இந்திய எழுத்தாளர்கள்",
        wiki="ta",
        depth=0,
        limit=50,
    )
    assert len(results) > 0
    # Premchand or Anant Pai should be found
    match = next((r for r in results if "பிரேம்சந்த்" in r.ta_title or "அனந்து" in r.ta_title), None)
    assert match is not None
