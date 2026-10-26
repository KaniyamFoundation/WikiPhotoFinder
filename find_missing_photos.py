#!/usr/bin/env python3
"""CLI tool to find Tamil Wikipedia articles that lack photos while their English counterparts have photos.

Usage examples:
    python3 find_missing_photos.py "பகுப்பு:இந்தியக் கணிதவியலாளர்கள்"
    python3 find_missing_photos.py "Category:Indian mathematicians" --wiki en
    python3 find_missing_photos.py "பகுப்பு:தமிழக விளையாட்டு வீரர்கள்" --depth 1 -o results.html
    python3 find_missing_photos.py "பகுப்பு:இந்திய எழுத்தாளர்கள்" --limit 50 --format md
"""

import argparse
import os
import sys
from typing import Optional

from wiki_photos import (
    WikiPhotoFinder,
    format_markdown,
    format_csv,
    format_json,
    format_html,
    print_rich_table,
    __version__,
)


def main():
    parser = argparse.ArgumentParser(
        description="Find Tamil Wikipedia articles missing photos where English Wikipedia has photos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check articles in a Tamil Wikipedia category
  %(prog)s "பகுப்பு:இந்தியக் கணிதவியலாளர்கள்"

  # Include 1 level of subcategories
  %(prog)s "பகுப்பு:தமிழக விளையாட்டு வீரர்கள்" --depth 1

  # Search using English category
  %(prog)s "Category:Tamil writers" --wiki en

  # Export results to an interactive HTML report
  %(prog)s "பகுப்பு:இந்திய எழுத்தாளர்கள்" -o missing_photos.html

  # Filter only photos already hosted on Wikimedia Commons
  %(prog)s "பகுப்பு:தமிழ்நாட்டு நபர்கள்" --commons-only
        """,
    )

    parser.add_argument(
        "category",
        nargs="?",
        help="Category name in Tamil (e.g. 'பகுப்பு:இந்திய எழுத்தாளர்கள்' or 'இந்திய எழுத்தாளர்கள்') or English (e.g. 'Category:Tamil writers')",
    )
    parser.add_argument(
        "-c", "--category-name",
        dest="category_opt",
        help="Alternative way to provide category name",
    )
    parser.add_argument(
        "-w", "--wiki",
        choices=["auto", "ta", "en"],
        default="auto",
        help="Category source wiki: 'ta' (ta.wikipedia.org), 'en' (en.wikipedia.org), or 'auto' (default: auto)",
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=0,
        help="Subcategory recursion depth (0 = root category only, 1 = 1 level of subcategories, etc. default: 0)",
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=0,
        help="Maximum number of articles to inspect (default: 0 for unlimited)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="File path to save results (e.g. output.html, output.md, output.csv, output.json)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["table", "md", "csv", "json", "html"],
        help="Force output format (default: auto-detected from --output filename, or 'table')",
    )
    parser.add_argument(
        "--commons-only",
        action="store_true",
        help="Only show photos hosted on Wikimedia Commons (ready to use immediately)",
    )
    parser.add_argument(
        "--check-linked-wikis",
        action="store_true",
        help="Check other language Wikipedia editions (via Wikidata) to see which also lack photos",
    )
    parser.add_argument(
        "--target-wikis",
        type=str,
        default="indic",
        help="Target languages to check: 'indic' (default: ml, te, kn, hi, bn, mr, etc.), 'all' (all linked wikis), or comma-separated list like 'ml,te,kn,hi'",
    )
    parser.add_argument(
        "-t", "--delay",
        type=float,
        default=1.0,
        help="Polite delay between API requests in seconds (default: 1.0s to respect Wikimedia servers)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout in seconds (default: 30.0s)",
    )
    parser.add_argument(
        "--maxlag",
        type=int,
        default=5,
        help="Wikimedia maxlag parameter for server load protection (default: 5s)",
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        help="Custom User-Agent header (defaults to tool name and bot username)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    category = args.category or args.category_opt
    if not category:
        parser.print_help()
        print("\n[Error] Please provide a category name.")
        sys.exit(1)

    limit = None if args.limit <= 0 else args.limit

    # Setup rich console / progress if available
    try:
        from rich.console import Console
        from rich.status import Status
        console = Console()
        use_rich = True
    except ImportError:
        console = None
        use_rich = False

    from wiki_photos.api import DEFAULT_USER_AGENT, MediaWikiClient
    from wiki_photos.wikidata import INDIC_WIKIS, DRAVIDIAN_WIKIS

    target_wikis = None
    if args.check_linked_wikis:
        tw = args.target_wikis.lower().strip()
        if tw == "all":
            target_wikis = ["all"]
        elif tw == "indic":
            target_wikis = INDIC_WIKIS
        elif tw == "dravidian":
            target_wikis = DRAVIDIAN_WIKIS
        else:
            target_wikis = [w.strip() for w in tw.split(",") if w.strip()]

    user_agent = args.user_agent
    if not user_agent:
        wiki_user = os.environ.get("WIKI_USER")
        if wiki_user:
            user_agent = f"WikiPhotoFinder/1.0 (https://ta.wikipedia.org/wiki/User:{wiki_user}; Tamil Wikipedia Photo Tool)"
        else:
            user_agent = DEFAULT_USER_AGENT

    client = MediaWikiClient(
        user_agent=user_agent,
        request_delay=args.delay,
        timeout=args.timeout,
        maxlag=args.maxlag,
    )
    finder = WikiPhotoFinder(client=client)

    status_spinner = None
    if use_rich:
        status_spinner = console.status("[bold cyan]Querying Wikipedia category members...")
        status_spinner.start()
    else:
        print(f"[*] Querying Wikipedia category: {category} (delay: {args.delay}s, timeout: {args.timeout}s)...")

    scanned_count = [0]

    def progress_callback(stage: str, current: int, total: int):
        if stage == "category_articles_total":
            scanned_count[0] = total

        if not use_rich or not status_spinner:
            if stage == "checking_ta_articles":
                print(f"[*] Checking Tamil articles: {current}/{total}...")
            elif stage == "checking_en_articles":
                print(f"[*] Checking English counterpart photos: {current}/{total}...")
            elif stage == "fetching_sitelinks":
                print("[*] Fetching linked language sitelinks from Wikidata...")
            elif stage.startswith("checking_") and stage.endswith("_wiki"):
                wiki_code = stage.split("_")[1]
                print(f"[*] Checking {wiki_code}.wikipedia.org photos: {current}/{total}...")
            return

        if stage == "crawling_category":
            status_spinner.update(f"[bold cyan]Traversing categories: {current} visited...")
        elif stage == "checking_ta_articles":
            status_spinner.update(f"[bold cyan]Checking Tamil Wikipedia articles: {current}/{total}...")
        elif stage == "checking_en_articles":
            status_spinner.update(f"[bold cyan]Checking English Wikipedia photos: {current}/{total}...")
        elif stage == "fetching_sitelinks":
            status_spinner.update("[bold cyan]Fetching linked language sitelinks from Wikidata...")
        elif stage.startswith("checking_") and stage.endswith("_wiki"):
            wiki_code = stage.split("_")[1]
            status_spinner.update(f"[bold cyan]Checking {wiki_code}.wikipedia.org articles for photos ({current}/{total} wikis)...")

    results = []
    try:
        results = finder.find_missing_photos(
            category=category,
            wiki=args.wiki,
            depth=args.depth,
            limit=limit,
            commons_only=args.commons_only,
            check_linked_wikis=args.check_linked_wikis,
            target_wikis=target_wikis,
            progress_callback=progress_callback,
        )
    except KeyboardInterrupt:
        if status_spinner:
            status_spinner.stop()
        msg = "\n[!] Process interrupted (Ctrl+C). Saving gathered results so far..."
        if use_rich:
            console.print(f"[bold yellow]{msg}[/]")
        else:
            print(msg)
    finally:
        if status_spinner:
            status_spinner.stop()

    # Determine output format
    fmt = args.format
    if not fmt:
        if args.output:
            ext = os.path.splitext(args.output)[1].lower()
            ext_map = {
                ".html": "html",
                ".htm": "html",
                ".md": "md",
                ".csv": "csv",
                ".json": "json",
            }
            fmt = ext_map.get(ext, "table")
        else:
            fmt = "table"

    # Generate content
    formatted_content: Optional[str] = None
    if fmt == "html":
        formatted_content = format_html(results, category)
    elif fmt == "md":
        formatted_content = format_markdown(results, category)
    elif fmt == "csv":
        formatted_content = format_csv(results)
    elif fmt == "json":
        formatted_content = format_json(results)

    # Save to file or print
    if args.output and formatted_content is not None:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted_content)
        if use_rich:
            console.print(f"[bold green]✓[/] Saved {len(results)} results to [bold]{args.output}[/]")
        else:
            print(f"Saved {len(results)} results to {args.output}")

    # If format is table, or if no output file was given, display table on console
    if fmt == "table" or not args.output:
        if results:
            print_rich_table(results, category)
            commons_count = sum(1 for r in results if r.is_on_commons)
            summary_msg = f"Scanned {scanned_count[0]} articles in category. Found {len(results)} articles missing photos in Tamil Wiki ({commons_count} available on Commons)."
            if use_rich:
                console.print(f"[bold cyan]{summary_msg}[/]")
            else:
                print(summary_msg)
        else:
            msg = f"Scanned {scanned_count[0]} articles in category '{category}'. No missing photos found (all articles either already have photos or lack English photos)."
            if use_rich:
                console.print(f"[bold yellow]{msg}[/]")
            else:
                print(msg)


if __name__ == "__main__":
    main()
