"""Unit tests for multi-wiki language discovery and updating."""

import unittest
from unittest.mock import MagicMock, patch
from wiki_photos.models import ArticleResult
from wiki_photos.wikidata import WikidataClient, INDIC_WIKIS
from wiki_photos.updater import WikiUpdater, MultiWikiUpdater, WIKI_IMAGE_PREFIXES
from wiki_photos.finder import WikiPhotoFinder


class TestMultiWiki(unittest.TestCase):
    def test_article_result_multi_wiki(self):
        result = ArticleResult(
            ta_title="அர்ச்சனா",
            en_title="Archana",
            image_name="Archana.jpg",
            wikidata_id="Q3531820",
            linked_wikis={
                "ml": {"wiki": "ml", "title": "അർച്ചന", "has_image": False},
                "te": {"wiki": "te", "title": "అర్చన", "has_image": False},
                "kn": {"wiki": "kn", "title": "ಅರ್ಚನಾ", "has_image": True},
            },
        )
        self.assertIn("ta", result.missing_wikis)
        self.assertIn("ml", result.missing_wikis)
        self.assertIn("te", result.missing_wikis)
        self.assertNotIn("kn", result.missing_wikis)

        self.assertIn("en", result.present_wikis)
        self.assertIn("kn", result.present_wikis)
        self.assertNotIn("ml", result.present_wikis)

        d = result.to_dict()
        self.assertEqual(d["missing_wikis"], ["ta", "ml", "te"])
        self.assertEqual(d["present_wikis"], ["en", "kn"])

    def test_wikidata_sitelinks(self):
        client = WikidataClient()
        fake_response = {
            "entities": {
                "Q100": {
                    "sitelinks": {
                        "enwiki": {"site": "enwiki", "title": "English Title"},
                        "tawiki": {"site": "tawiki", "title": "Tamil Title"},
                        "mlwiki": {"site": "mlwiki", "title": "Malayalam Title"},
                        "tewiki": {"site": "tewiki", "title": "Telugu Title"},
                        "commonswiki": {"site": "commonswiki", "title": "Commons Title"},
                        "metawiki": {"site": "metawiki", "title": "Meta Title"},
                        "dewikisource": {"site": "dewikisource", "title": "Source Title"},
                    }
                }
            }
        }
        with patch.object(client.mw_client, "_post", return_value=fake_response):
            links = client.get_sitelinks(["Q100"])
            self.assertIn("Q100", links)
            sitelinks = links["Q100"]
            self.assertEqual(sitelinks.get("en"), "English Title")
            self.assertEqual(sitelinks.get("ta"), "Tamil Title")
            self.assertEqual(sitelinks.get("ml"), "Malayalam Title")
            self.assertEqual(sitelinks.get("te"), "Telugu Title")
            # Ensure excluded projects are not present
            self.assertNotIn("commons", sitelinks)
            self.assertNotIn("meta", sitelinks)
            self.assertNotIn("dewikisource", sitelinks)

    def test_wikidata_sitelinks_filtered(self):
        client = WikidataClient()
        fake_response = {
            "entities": {
                "Q100": {
                    "sitelinks": {
                        "enwiki": {"site": "enwiki", "title": "English Title"},
                        "tawiki": {"site": "tawiki", "title": "Tamil Title"},
                        "mlwiki": {"site": "mlwiki", "title": "Malayalam Title"},
                        "frwiki": {"site": "frwiki", "title": "French Title"},
                    }
                }
            }
        }
        with patch.object(client.mw_client, "_post", return_value=fake_response):
            links = client.get_sitelinks(["Q100"], target_wikis=["ta", "ml"])
            sitelinks = links["Q100"]
            self.assertIn("ta", sitelinks)
            self.assertIn("ml", sitelinks)
            self.assertNotIn("fr", sitelinks)
            self.assertNotIn("en", sitelinks)

    def test_wiki_updater_localized_prefixes(self):
        self.assertEqual(WIKI_IMAGE_PREFIXES.get("ta"), "படிமம்")
        self.assertEqual(WIKI_IMAGE_PREFIXES.get("ml"), "പ്രമാണം")
        self.assertEqual(WIKI_IMAGE_PREFIXES.get("te"), "దస్త్రం")
        self.assertEqual(WIKI_IMAGE_PREFIXES.get("kn"), "ಚಿತ್ರ")
        self.assertEqual(WIKI_IMAGE_PREFIXES.get("hi"), "चित्र")
        self.assertEqual(WIKI_IMAGE_PREFIXES.get("bn"), "চিত্র")

    def test_wiki_updater_apply_image_malayalam(self):
        content = "{{Infobox person\n| name = അർച്ചന\n| image = \n}}"
        updated = WikiUpdater.apply_image_to_wikitext(content, "അർച്ചന", "Archana.jpg", wiki="ml")
        self.assertIn("| image = Archana.jpg", updated)

    def test_wiki_updater_apply_lead_image_telugu(self):
        content = "'''అర్చన''' ఒక ప్రముఖ నటి."
        updated = WikiUpdater.apply_image_to_wikitext(content, "అర్చన", "Archana.jpg", wiki="te")
        self.assertTrue(updated.startswith("[[దస్త్రం:Archana.jpg|thumb|అర్చన]]\n\n"))

    def test_wiki_updater_apply_lead_image_hindi(self):
        content = "'''अर्चना''' एक भारतीय अभिनेत्री हैं।"
        updated = WikiUpdater.apply_image_to_wikitext(content, "अर्चना", "Archana.jpg", wiki="hi")
        self.assertTrue(updated.startswith("[[चित्र:Archana.jpg|thumb|अर्चना]]\n\n"))

    def test_multi_wiki_updater_session_cache(self):
        multi = MultiWikiUpdater()
        multi.set_credentials("MyUser@Bot", "mypassword")

        with patch.object(WikiUpdater, "login", return_value=True) as mock_login:
            up_ta = multi.get_updater("ta")
            up_ml = multi.get_updater("ml")
            up_ta_again = multi.get_updater("ta")

            self.assertEqual(up_ta.wiki, "ta")
            self.assertEqual(up_ml.wiki, "ml")
            self.assertIs(up_ta, up_ta_again)
            self.assertEqual(mock_login.call_count, 2)

    def test_finder_check_linked_wikis(self):
        finder = WikiPhotoFinder()
        result = ArticleResult(
            ta_title="அர்ச்சனா",
            en_title="Archana",
            image_name="Archana.jpg",
            wikidata_id="Q3531820",
        )

        mock_sitelinks = {
            "Q3531820": {
                "ml": "അർച്ചന",
                "te": "అర్చన",
            }
        }
        mock_page_info_ml = {
            "അർച്ചന": {"has_image": False, "missing": False, "image_name": None}
        }
        mock_page_info_te = {
            "అర్చన": {"has_image": True, "missing": False, "image_name": "Local.jpg"}
        }

        def mock_get_pages_info(wiki, titles):
            if wiki == "ml":
                return mock_page_info_ml
            elif wiki == "te":
                return mock_page_info_te
            return {}

        with patch.object(WikidataClient, "get_sitelinks", return_value=mock_sitelinks):
            with patch.object(finder.client, "get_pages_info", side_effect=mock_get_pages_info):
                finder.check_linked_wikis_for_results([result], target_wikis=["ml", "te"])

                self.assertIn("ml", result.linked_wikis)
                self.assertIn("te", result.linked_wikis)
                self.assertFalse(result.linked_wikis["ml"]["has_image"])
                self.assertTrue(result.linked_wikis["te"]["has_image"])
                self.assertIn("ml", result.missing_wikis)
                self.assertNotIn("te", result.missing_wikis)
