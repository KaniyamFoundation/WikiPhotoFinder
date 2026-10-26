"""Terminal image preview utility using chafa (sixel / symbols)."""

import os
import shutil
import subprocess
import sys
from typing import Optional
import requests


def has_chafa() -> bool:
    """Check if the chafa binary is installed."""
    return shutil.which("chafa") is not None


def show_terminal_image(
    image_url: str,
    user_agent: str,
    image_format: str = "sixel",
    size: str = "45x25",
    timeout: float = 15.0,
) -> bool:
    """Download image and display it directly in the terminal using chafa.

    Args:
        image_url: Direct URL to image or thumbnail
        user_agent: User-Agent header for Wikimedia CDN
        image_format: 'sixel', 'symbols', 'auto', or 'none'
        size: Terminal geometry, e.g. '45x25'
        timeout: Download timeout in seconds

    Returns:
        True if image was displayed successfully, False otherwise.
    """
    if image_format.lower() == "none" or not has_chafa():
        return False

    if not image_url:
        return False

    try:
        headers = {"User-Agent": user_agent}
        res = requests.get(image_url, headers=headers, timeout=timeout)
        if res.status_code != 200 or not res.content:
            return False

        # Run chafa
        cmd = ["chafa", "-f", image_format, "--size", size, "-"]
        proc = subprocess.run(
            cmd,
            input=res.content,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        if proc.returncode == 0 and proc.stdout:
            sys.stdout.buffer.write(b"\n")
            sys.stdout.buffer.write(proc.stdout)
            sys.stdout.buffer.write(b"\n")
            sys.stdout.flush()
            return True
        return False

    except Exception:
        # If terminal rendering fails, fail silently and allow text diff to display
        return False
