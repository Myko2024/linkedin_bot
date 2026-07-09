# LinkedIn engagement prototype

**Level reached:** 3 (profile-aware comment drafts).
**Time:** ~2h of build, plus a rewrite of the whole scraping layer after
LinkedIn's feed DOM turned out to be freshly obfuscated (see below).

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env          # put a VALID ANTHROPIC_API_KEY in .env for L2/L3
python main.py | tee sample_output.txt
```

First run opens a Chromium window — **log in to LinkedIn manually** (you have 5 min).
The session persists in `./user_data/`, so later runs go straight to the feed.

Offline test suite (no LinkedIn, no API key needed):

```bash
python test_logic.py          # scoring, count parsing, AI prompt shape + mocked draft
```

## Project structure

The code is split into concern-based packages, each depending only on the ones
below it:

```
main.py                  entrypoint: build objects, run the manager
engagement/
  manager.py             orchestration: wire LinkedIn + AI + scoring, print results
  linkedin/              domain: what to DO on LinkedIn (login / read+like / profile)
    client.py              the LinkedIn action class
    selectors.py           obfuscation-proof CSS selectors
    scripts.py             in-page JavaScript scrapers
    parsing.py             raw scrape dict -> Post
  ai/                    domain: draft human-sounding comments (Anthropic)
    writer.py              the API client (CommentWriter)
    prompts.py             the prompt template + builder
  scoring/               domain: the "interesting" rule (pure, unit-tested)
    rules.py               score_post
    text.py                parse_count and other text helpers
  browser/               generic Playwright wrapper (find / click / scroll / eval / tabs)
    driver.py              the Browser class
  models.py              the Post dataclass
  config.py              env-driven configuration
```

- **`browser/`** knows nothing about LinkedIn — just "how to drive a browser".
- **`linkedin/`** owns every site-specific detail — selectors, in-page JS, and
  what a "Like" means are each their own module — and drives the site through `Browser`.
- **`ai/`** owns the comment prompt + API call (and exposes `build_prompt` so the
  manager can print it in "assistant mode" when there's no key).
- **`manager.py`** is the only layer that knows the three task "levels"; it holds no
  Playwright, no selectors, no API calls of its own.

Useful env flags: **`DRY_RUN=1`** scores/prints without clicking Like (set it to
`0` — the current default — to place **real** likes); `TOP_N` = how many to like;
`LIKE_MIN_SCORE` = only like posts scoring above this (default 0, i.e. any
non-bait post); `PROFILE_AWARE=0` stops at Level 2; `COMMENT_N=0` stops at
Level 1; `FEED_URL=https://www.linkedin.com/feed/hashtag/python/` scrapes a
hashtag feed instead of the (often sparse) home feed.

## Design choices (short version)

- **No automated login, no credentials in code.** Manual login into a persistent
  Playwright context is safer (nothing to leak) and far less likely to trip
  LinkedIn's bot detection than typing credentials with a robot. Same reason the
  browser is headful and every action has randomized delays.
- **"Interesting" rule** (`score_post`, priority order): never ads → substance
  (capped text length) → relevance (interest keywords, capped at 3 so stuffing
  can't game it) → log-scaled reaction count → penalty for sub-120-char
  one-liners → penalty for **engagement-bait** (link-dump listicles, "100% FREE",
  arrow-bait ⤵️/👇). Log scaling stops viral one-liners from beating substantive
  niche posts; the bait penalty stops long-but-worthless spam from ranking on
  length alone (a "5 remote-job sites" listicle in the sample scored -0.26 and
  was dropped). The top `COMMENT_N` scoring > 0 become comment candidates.
- **Comments are drafted, never posted.** The prompt bans the usual AI tells
  (praise openers, "This resonates", emojis, em-dashes) and forces a reaction to
  one concrete point in under 40 words, in a stated persona voice.
- **No key? "Assistant mode."** With a valid `ANTHROPIC_API_KEY` the script
  drafts automatically. Without one, it prints the exact per-post prompt for you
  to paste into whatever AI assistant you use — the task explicitly allows "any
  AI assistant you actually use," and this keeps the pipeline useful either way.
- **Level 3** feeds the author's headline (captured from the feed byline) plus
  name (from the profile page) into the drafting prompt so the comment can
  reference shared ground.

## Honest caveat

Automated feed interaction violates LinkedIn's User Agreement and can get an
account restricted. This is a test-task prototype: keep `DRY_RUN=1`, keep volumes
tiny, ideally use a throwaway account. The obfuscated-DOM selectors above were
verified 2026-07-09 and **will** rot on LinkedIn's next deploy.
