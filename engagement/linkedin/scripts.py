"""In-page JavaScript run inside the LinkedIn tab.

These are the obfuscation-proof scrapers: given a reaction button, climb to its
post container and read the post out of THAT SAME container; and, on a profile
page, pull a name + headline without relying on semantic markup.
"""
from __future__ import annotations

# Given a reaction button, climb to its post container and read the post out of
# THAT SAME container -- so scoring and clicking use one element (no fragile
# "match this button to a separately-scraped post" step). The headline (`sub`)
# comes from the feed byline: the longest clean line that isn't actor chrome
# (anything with a "•"/"·" bullet or a URL) -- real headlines use "|" separators.
POST_FROM_BTN_JS = r"""(btn) => {
  let node = btn, c = null;
  for (let i = 0; i < 14 && node; i++) {
    node = node.parentElement; if (!node) break;
    if (node.querySelector("a[href*='/in/'], a[href*='/company/']") &&
        node.querySelector("button[aria-label^='Reaction button state']")) { c = node; break; }
  }
  if (!c) return null;
  let author = "", href = null;
  for (const a of c.querySelectorAll("a[href*='/in/'], a[href*='/company/']")) {
    const t = (a.innerText || "").trim().replace(/\s+/g, " ");
    if (t) { author = t.split("•")[0].split("\n")[0].trim(); href = a.getAttribute("href").split("?")[0]; break; }
  }
  let sub = "";
  {
    const bad = new Set(["Feed post", "Following", "… more", "…", "more"]);
    const cand = [];
    for (const el of c.querySelectorAll("span, div, p")) {
      const t = (el.innerText || "").trim().replace(/\s+/g, " ");
      if (t && t.length >= 8 && t.length <= 160 && !cand.includes(t)) cand.push(t);
      if (cand.length >= 20) break;
    }
    for (const t of cand.sort((a, b) => b.length - a.length)) {
      if (bad.has(t)) continue;
      if (author && t.startsWith(author)) continue;      // the name / combined blob
      if (t.includes("•") || t.includes("·")) continue;  // actor chrome, not a headline
      if (!/\s/.test(t)) continue;                       // single token => URL/domain/handle
      if (/https?:\/\/|lnkd\.in|www\.|\.(com|co|io|ai|net|org|dev|app|google|xyz)\b/i.test(t)) continue;
      if (/^\d+\s*[smhdwy]?$/i.test(t)) continue;        // a bare timestamp
      sub = t; break;
    }
  }
  const comm = c.querySelector("[componentkey^='feed-commentary_']");
  const text = comm ? (comm.innerText || "").trim().replace(/\s+/g, " ") : "";
  const reactions = (btn.innerText || "").trim();
  const reacted = !/no reaction/i.test(btn.getAttribute("aria-label") || "");
  const promoted = /\bpromoted\b/i.test((c.innerText || "").slice(0, 300));
  return { author, sub, href, text: text.slice(0, 1500), reactions, reacted, promoted };
}"""

# Profile pages are obfuscated too (no h1, empty meta when logged in). Take the
# name from <title> and the headline as the first clean line near the top,
# stopping before any "People you may know" block so we can't grab a stranger.
PROFILE_CONTEXT_JS = r"""() => {
  const title = (document.title || "").replace(/\s*\|\s*LinkedIn.*$/, "").trim();
  const STOP = /people you may know|others named|more profiles|people also viewed/i;
  const SKIP = /followers|connections|contact info|·|following$/i;
  const nodes = (document.querySelector("main") || document.body)
                  .querySelectorAll("div, span, h2, p");
  let count = 0, headline = "";
  for (const n of nodes) {
    if (count++ > 350) break;
    const t = (n.innerText || "").trim().replace(/\s+/g, " ");
    if (STOP.test(t)) break;
    if (t.length < 15 || t.length > 200) continue;
    if (SKIP.test(t)) continue;
    if (title && t.startsWith(title)) continue;
    headline = t; break;
  }
  return { title, headline };
}"""
