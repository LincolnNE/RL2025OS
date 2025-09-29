"""
Instagram Tools Source Package
"""

__version__ = "1.0.0"
__author__ = "Abric Util Manager"

# Convenience imports for main.py
from .instagram_api import InstagramAPI
from .instagram_rapidapi import InstagramRapidAPI
from .instagram_account_finder import InstagramAccountFinder
from .batch_downloader import BatchDownloader

__all__ = [
    'InstagramAPI',
    'InstagramRapidAPI', 
    'InstagramAccountFinder',
    'BatchDownloader'
]
