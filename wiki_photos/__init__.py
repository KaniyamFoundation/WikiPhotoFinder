"""WikiPhotoFinder: Tool to find Tamil Wikipedia articles missing photos

where English Wikipedia articles have photos.
"""

from .models import ArticleResult
from .api import MediaWikiClient
from .finder import WikiPhotoFinder
from .updater import TamilWikiUpdater, WikiUpdater, MultiWikiUpdater
from .wikidata import WikidataClient, INDIC_WIKIS, DRAVIDIAN_WIKIS
from .formatters import (
    format_markdown,
    format_csv,
    format_json,
    format_html,
    print_rich_table,
)

__version__ = "1.1.0"
__all__ = [
    "ArticleResult",
    "MediaWikiClient",
    "WikiPhotoFinder",
    "TamilWikiUpdater",
    "WikiUpdater",
    "MultiWikiUpdater",
    "WikidataClient",
    "INDIC_WIKIS",
    "DRAVIDIAN_WIKIS",
    "format_markdown",
    "format_csv",
    "format_json",
    "format_html",
    "print_rich_table",
]
