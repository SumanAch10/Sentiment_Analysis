# Reddit historical coverage without an API key

The requested window is January 2016 through December 2026 UTC. Use the same subreddit and keyword definitions in every source. For a ten-complete-year comparison, use 2016–2025 and treat 2026 separately.

## Data access and source coverage

- **Reddit for Researchers** gives approved university researchers access through BigQuery. Reddit documents a five-year historical window with a six-month delay, updated monthly. Check the earliest and latest dates in your assigned tables. A zero at either end can reflect missing source coverage. [Program documentation and application](https://support.reddithelp.com/hc/en-us/articles/49381918834964-Reddit-for-Researchers-Program)
- **Historical archive candidate.** The PushshiftDumps repository links to downloadable Reddit dumps. Before collecting from one, confirm its permitted research use, its months and communities, and how it handles content deleted after snapshotting. The processing examples and the archive are separate resources. Archive coverage, permission, and deletion handling have yet to be verified for this study. [Archive processing repository and download link](https://github.com/Watchful1/PushshiftDumps)
- **Overlap check.** If both sources are usable, run the same query on each source separately. Compare common months by subreddit and content type. Before combining records, check differences in selection and deduplicate using content type plus native ID. Record source changes and gaps with the results. Keep research source data in the approved environment and export aggregates only as permitted.

## BigQuery coverage query

Replace the two table references and the field names in the `records` CTE using the schema from your onboarding manual. This template assumes the timestamps are already BigQuery `TIMESTAMP` values. For epoch seconds, use `TIMESTAMP_SECONDS(created_utc)`. Expand the initial five-subreddit panel only if it matches your approved scope. The 15 phrases match the Bluesky and YouTube backfills.

The query emits monthly counts by subreddit and content type, including zero-count cells. It does not output post text or user identifiers. Use BigQuery's dry run after mapping the schema to check validity and estimated bytes. Apply a partition filter if your assigned tables use a separate partition column.

```sql
DECLARE start_month DATE DEFAULT DATE '2016-01-01';
DECLARE end_month_exclusive DATE DEFAULT DATE '2027-01-01';
DECLARE communities ARRAY<STRING> DEFAULT [
  'space', 'spacex', 'nasa', 'futurology', 'askreddit'
];
DECLARE topic_pattern STRING DEFAULT
  r'\b(space\s+travel|space\s+exploration|spaceflight|space\s+program|going\s+to\s+space|multi[-\s]?planetary|interplanetary|mars\s+colony|coloni[sz]e\s+mars|mars\s+mission|living\s+on\s+mars|space\s+touris[mt])\b';

WITH records AS (
  SELECT
    'post' AS content_type,
    CAST(id AS STRING) AS native_id,
    LOWER(subreddit) AS subreddit,
    created_utc AS created_at,
    CONCAT(COALESCE(title, ''), ' ', COALESCE(body, '')) AS content
  FROM `YOUR_PROJECT.YOUR_DATASET.YOUR_POSTS_TABLE`
  UNION ALL
  SELECT
    'comment',
    CAST(id AS STRING),
    LOWER(subreddit),
    created_utc,
    COALESCE(body, '')
  FROM `YOUR_PROJECT.YOUR_DATASET.YOUR_COMMENTS_TABLE`
),
counts AS (
  SELECT
    DATE_TRUNC(DATE(created_at, 'UTC'), MONTH) AS month,
    subreddit,
    content_type,
    COUNT(DISTINCT native_id) AS available_items,
    COUNT(DISTINCT IF(
      REGEXP_CONTAINS(LOWER(content), topic_pattern), native_id, NULL
    )) AS topic_matches
  FROM records
  WHERE created_at >= TIMESTAMP(start_month, 'UTC')
    AND created_at < TIMESTAMP(end_month_exclusive, 'UTC')
    AND subreddit IN UNNEST(communities)
  GROUP BY month, subreddit, content_type
),
grid AS (
  SELECT month, subreddit, content_type
  FROM UNNEST(GENERATE_DATE_ARRAY(
    start_month, DATE_SUB(end_month_exclusive, INTERVAL 1 MONTH), INTERVAL 1 MONTH
  )) AS month
  CROSS JOIN UNNEST(communities) AS subreddit
  CROSS JOIN UNNEST(['post', 'comment']) AS content_type
)
SELECT
  month, subreddit, content_type,
  COALESCE(available_items, 0) AS available_items,
  COALESCE(topic_matches, 0) AS topic_matches
FROM grid
LEFT JOIN counts USING (month, subreddit, content_type)
ORDER BY month, subreddit, content_type;
```

Keep the aggregate counts with the source's documented coverage dates and the query date. Compare months with sufficient topical matches after checking which months were actually present in each source.
