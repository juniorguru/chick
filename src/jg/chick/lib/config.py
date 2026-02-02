"""Centralized configuration constants for the Chick Discord bot.

This module contains all Discord IDs, API URLs, and other configuration
constants used throughout the application. Centralizing these values
makes it easier to maintain and update them.
"""

import os
from datetime import timedelta


# =============================================================================
# Discord Role IDs
# =============================================================================

#: Role ID for greeters who welcome new members in #ahoj
GREETER_ROLE_ID = 1062755787153358879

#: Role ID for reviewers who provide feedback on CV/GitHub/LinkedIn
REVIEWER_ROLE_ID = 1075044541796716604

#: Discord user ID of the bot maintainer for error reports
MAINTAINER_ID = 668226181769986078


# =============================================================================
# Discord Channel IDs
# =============================================================================

#: Channel ID for reporting errors related to interest fetching
ERROR_REPORT_CHANNEL_ID = 1135903241792651365


# =============================================================================
# Discord Channel Names
# =============================================================================

#: Channel name for introductions
CHANNEL_AHOJ = "ahoj"

#: Channel name for daily pitfalls/traps discussion
CHANNEL_PAST_VEDLE_PASTI = "past-vedle-pasti"

#: Channel name for daily discoveries
CHANNEL_MUJ_DNESNI_OBJEV = "můj-dnešní-objev"

#: Channel name for job postings
CHANNEL_PRACE_INZERATY = "práce-inzeráty"

#: Channel name for job seekers
CHANNEL_PRACE_HLEDAM = "práce-hledám"

#: Channel name for CV/GitHub/LinkedIn reviews
CHANNEL_CV_GITHUB_LINKEDIN = "cv-github-linkedin"


# =============================================================================
# API URLs
# =============================================================================

#: URL for fetching candidate profiles from eggtray
EGGTRAY_API_URL = "https://juniorguru.github.io/eggtray/profiles.json"

#: URL for fetching interest thread data
INTERESTS_API_URL = "https://junior.guru/api/interests.json"


# =============================================================================
# API Keys
# =============================================================================

#: GitHub API key for enhanced profile analysis (optional)
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY") or None


# =============================================================================
# Timing Constants
# =============================================================================

#: Cooldown period between notifications to the same role in interest threads
NOTIFICATION_COOLDOWN = timedelta(days=1)

#: Interval for refreshing interest data from the API
INTERESTS_REFRESH_INTERVAL_HOURS = 6


# =============================================================================
# Thread Naming
# =============================================================================

#: Czech day names for thread naming (Monday through Sunday)
DAYS = [
    "Pondělní",  # Monday
    "Úterní",    # Tuesday
    "Středeční", # Wednesday
    "Čtvrteční", # Thursday
    "Páteční",   # Friday
    "Sobotní",   # Saturday
    "Nedělní",   # Sunday
]

#: Template for naming introduction threads
INTRO_THREAD_NAME_TEMPLATE = "Ahoj {author}!"
