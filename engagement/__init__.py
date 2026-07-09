"""LinkedIn engagement prototype -- decomposed into concern-based packages.

Each layer depends only on the ones below it:

    main.py                  entrypoint: build objects, run the manager
      manager.py             orchestration: wire LinkedIn + AI + scoring, print results
        linkedin/            domain: what to DO on LinkedIn (login / read+like / profile)
          client.py            the LinkedIn action class
          selectors.py         obfuscation-proof CSS selectors
          scripts.py           in-page JavaScript scrapers
          parsing.py           raw scrape dict -> Post
        ai/                  domain: draft human-sounding comments (Anthropic)
          writer.py            the API client (CommentWriter)
          prompts.py           the prompt template + builder
        scoring/             domain: the "interesting" rule (pure, unit-tested)
          rules.py             score_post
          text.py              parse_count and other text helpers
          browser/           generic Playwright wrapper (find / click / scroll / eval)
            driver.py          the Browser class
          models.py          the Post dataclass
          config.py          env-driven configuration
"""
