# Research log

Dated notes and decisions. Newest at the bottom.

## 2026-11-16
- Received FAA comment file: ~17,043 public comments on the 2021 Draft PEA (SpaceX Starship/Super Heavy, Boca Chica). Sept–Nov 2021. ~15% duplicates/templates, OCR noise, volumes 16–18 and 20 missing.

## 2026-11-17
- Decided: start with descriptive sentiment analysis of social media posts about space travel. No research question or framework yet; dig deeper once sentiment results are in.
- Project folder and plans created. No code yet.

## 2026-11-18
- Ran a pilot for 2026-08-21 through 2026-11-18 UTC. Bluesky returned 625 unique posts across 26 keyword searches (one page per query, newest results first, English search filter). YouTube and Reddit were skipped because credentials were unavailable.
- The collector uses the official platform APIs and records exact query terms, the UTC window, and per-source status in each run manifest. The pilot data and author salt were kept outside GitHub.
- Backfilled Bluesky month by month from November 2025 through October 2026 UTC. Used the same 15 terms from the general, multiplanetary, and tourism groups for each month, one page of up to 25 English search results per term, newest first. All 180 searches completed and yielded 3,791 unique posts (287–340 per month). Per-month coverage and query manifests are stored with the private dataset. Search caps and newest-first ordering can skew coverage within a month.
- Extended the same monthly Bluesky collection back to January 2024. Verified 10,160 unique posts across 34 complete calendar months through October 2026 (3,166 in 2024; 3,796 in 2025; 3,198 in January–October 2026). The combined dataset and monthly and yearly coverage tables remain in the private workspace. The one-page-per-query cap still applies.
