"""CSS selectors that survive LinkedIn's obfuscation.

DOM note (2026-07): LinkedIn's feed is a fully-obfuscated, virtualized React app.
Every semantic class (feed-shared-update-v2, react-button__trigger, ...) is gone,
replaced by build-hash names, and only a handful of posts live in the DOM at once.
So we anchor exclusively on things that survive obfuscation: `componentkey`
prefixes, `aria-label` prefixes, and profile `href`s.
"""
from __future__ import annotations

COMMENTARY_SEL = "[componentkey^='feed-commentary_']"        # each post's text block
REACT_BTN = "button[aria-label^='Reaction button state']"    # the Like toggle

# Signals that we're logged in and on a real feed (obfuscation-proof):
LOGGED_IN_SEL = (
    "button:has-text('Start a post'), "
    "[componentkey='container-update-list_mainFeed-lazy'], " + COMMENTARY_SEL
)
# A narrower "the feed is really here" signal, used when waiting out a manual login.
FEED_READY_SEL = (
    "button:has-text('Start a post'), "
    "[componentkey='container-update-list_mainFeed-lazy']"
)
LOGIN_FORM_SEL = "input[name='session_key'], input[type='password']"
