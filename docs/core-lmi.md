# Explore the labor market with Core LMI

Core LMI (also called **Agnitio**) adds employment, earnings, industry, education, and regional measures to the server. It uses your existing Lightcast credentials with the `agnitio` scope. Start with dataset discovery: the catalog reflects your contract.

During the November 12, 2026 review, the account exposed **52 datasets**. Data queries were verified for **occupation**, **industry**, and **education completions**, including the examples below. The available releases included **2026.4**. Those are observations from this review, not defaults or a promise that another account has the same access.

## Questions you can ask

| Ask your assistant | What it can do |
| --- | --- |
| “Compare software-developer employment and median annual earnings in California and Washington.” | Retrieve the same occupation and worker classes for both states. |
| “How many restaurant jobs are in King and Kitsap counties combined?” | Aggregate a custom region and retrieve jobs and establishments. |
| “Are restaurants especially concentrated in King County?” | Calculate a location quotient against the national industry mix. |
| “What explains the change in local restaurant employment?” | Request shift-share components over a specified time interval. |
| “How many computer-science bachelor’s awards did UW Seattle report?” | Query completions by institution, program, and award level. |

Core LMI measures and projections differ from online job advertisements. Use Job Postings tools for advertised demand, and Core LMI for the measures described by the selected dataset.

## Discover → inspect → query

1. Call `list_core_lmi_datasets` with `{"query":"occupation"}`. Set `include_definitions: true` to also search descriptions. Follow `pagination.next_offset` if more entries remain.
2. Call `get_core_lmi_versions` with the returned dataset name. `latest_numeric` selects the newest numeric release regardless of the API’s array order. Special releases such as `base` and `example` require explicit selection.
3. Call `get_core_lmi_metadata` with that dataset and release. Inspect `attributes`, `dimensions`, and `metrics`. Filter metrics using `metric_query`, and page through `metrics_pagination`.
4. Call `get_core_lmi_dimension` to find exact codes. Choose **search** or **hierarchy filters** (`level`, `aggregation_path`) in a call. Preserve the returned `child` code exactly; different taxonomies use different code formats.
5. Call `query_core_lmi`, pinning the release you inspected.

For example, inspect available earnings metrics:

```json
{
  "dataset": "emsi.us.occupation",
  "version": "2026.4",
  "metric_query": "Earnings.",
  "limit": 20
}
```

Find the occupation code with `get_core_lmi_dimension`:

```json
{
  "dataset": "emsi.us.occupation",
  "version": "2026.4",
  "dimension": "Occupation",
  "search": "Software Developers"
}
```

The live response identified `15-1252`. Area discovery identified California as `6` and Washington as `53`. These are Core LMI codes, so use the discovered values instead of borrowing IDs from Titles or LOT.

!!! tip "Release date and measure year are different"
    Release `2026.4` reported `currentYear: 2025` for occupation and industry data. `Jobs.2030` is a projection, while the unsuffixed `Earnings.Median.Annual` resolves to the release’s earnings year. Read attributes and returned column names, and state both the release and measure year in your analysis.

## Compare employment and annual earnings

Tool: **`query_core_lmi`**. This request returns one row per state. The worker group includes QCEW and non-QCEW employees; self-employed workers and extended proprietors are excluded by this explicit selection.

```json
{
  "dataset": "emsi.us.occupation",
  "version": "2026.4",
  "query": {
    "metrics": [
      {"name": "Jobs.2025"},
      {"name": "Jobs.2030"},
      {"name": "Earnings.Median.Annual"}
    ],
    "constraints": [
      {"dimensionName": "Area", "map": {"California": ["6"], "Washington": ["53"]}},
      {"dimensionName": "Occupation", "map": {"Software Developers": ["15-1252"]}},
      {"dimensionName": "ClassOfWorker", "map": {"Employees": ["1", "2"]}}
    ],
    "sortBy": [{"name": "Area", "direction": "ascending"}],
    "limit": 10
  }
}
```

Interpret the units from metadata. Annual earnings, hourly earnings, total industry earnings, job counts, and advertised salaries answer different questions. Keep missing or suppressed values as missing; do not convert them to zero.

## Build a custom regional industry view

This verified query combines two counties into one region. Each key under `map` becomes an output label, while its array defines the codes to aggregate.

```json
{
  "dataset": "emsi.us.industry",
  "version": "2026.4",
  "query": {
    "metrics": [{"name": "Jobs.2025"}, {"name": "Establishments.2025"}],
    "constraints": [
      {"dimensionName": "Area", "map": {"King + Kitsap counties": ["53033", "53035"]}},
      {"dimensionName": "Industry", "map": {"Full-Service Restaurants": ["722511"]}},
      {"dimensionName": "ClassOfWorker", "map": {"Employees": ["1", "2"]}}
    ],
    "limit": 10
  }
}
```

For separate counties, use separate map labels. For a hierarchy expansion, the verified industry query also accepts `{"dimensionName":"Area","mapLevel":{"level":3,"predicate":[53]}}` to request Washington counties. Select small pages when expanding a hierarchy.

## Investigate concentration and change

Keep the industry and worker constraints above, and use one area: `{"King County, WA":["53033"]}`. Replace `metrics` with:

```json
[
  {
    "name": "Jobs.2025",
    "as": "Concentration",
    "operation": {"name": "LocationQuotient", "geoparent": "0", "along": "Industry"}
  },
  {
    "name": "Jobs.2025",
    "as": "Change factors",
    "operation": {"name": "ShiftShare", "geoparent": "0", "along": "Industry", "base": "Jobs.2020"}
  }
]
```

Both operations passed live testing. Shift share returns multiple component columns; preserve their returned labels rather than treating the operation as a single scalar. The national comparison is selected with `geoparent: "0"`.

## Examine education completions

This verified example requests computer-science bachelor’s completions at UW Seattle. Institution, program, and award codes were checked through dimension discovery.

```json
{
  "dataset": "emsi.us.completers",
  "version": "2026.4",
  "query": {
    "metrics": [{"name": "Completions.2025"}],
    "constraints": [
      {"dimensionName": "Unit", "map": {"UW Seattle": ["236948"]}},
      {"dimensionName": "Program", "map": {"Computer Science": ["11.0701"]}},
      {"dimensionName": "AwardLevel", "map": {"Bachelors": ["5"]}}
    ],
    "limit": 10
  }
}
```

Use the dataset’s definitions when choosing between `Completions` and `Completers`. Award counts and counts of people are different measures.

## Read and page results correctly

`data` is **column-oriented**. Each column has `name`, `type`, and `rows`; values at the same index form one record. The wrapper preserves upstream columns, extra response fields, errors, timings, and release provenance.

Queries return at most **500 rows per page** (100 by default), with at most 20 metrics. This server exposes a bounded window of the first **5,000 rows**. Narrow the dimensions for larger analyses.

Live testing found that the upstream service ignored `offset` and reported `totalRows` for the limited response. To prevent duplicate pages, the wrapper requests a prefix of `offset + limit + 1` rows, sets the upstream offset to zero, and slices the requested page locally. The extra row detects whether more results exist. Later pages re-fetch the prefix and therefore cost more work than the first page.

- Keep the dataset, release, filters, and `sortBy` identical between pages. Use enough sorting dimensions to disambiguate rows.
- Set `query.offset` to `pagination.next_offset`; nonzero offsets require `sortBy`.
- `pagination.returned` is the delivered row count; `fetched` includes the prefix and lookahead.
- `totalRows` is preserved as upstream metadata. `pagination.total` is null because it is not an authoritative count of all matching rows.
- If `has_more` is true but `next_offset` is null, the 5,000-row window is exhausted. Narrow the query.
- Metadata pagination happens locally too; hierarchy filters reduce the upstream metadata response.

## Known service limitation

The account can discover `emsi.us.costoflivingindex`, its `COLI` metric, and area codes. Data requests using the documented `map`, `mapLevel`, and `asIdentity` forms returned HTTP 400 during this review. One response requested `mapChildren`, which is absent from the current published query schema. This integration does not invent that undocumented contract or claim cost-of-living data queries passed. Resolve this discrepancy with Lightcast before relying on that dataset’s query results.

## Re-run the live checks

```bash
uv run python -m mcp_lightcast.diagnostics --core-lmi --output test-results/core-lmi-live-results.json
```

This explicitly uses your credentials and consumes quota. The report contains outcomes, release metadata, and the accessible dataset count, without credentials or market values. Core LMI requests are spaced at one per second by default, consistent with the documented 300 requests per five minutes.

## Official references

[Service overview and quota](https://docs.lightcast.io/lightcast-api/reference/overview-core-lmi), [dataset catalog](https://docs.lightcast.io/lightcast-api/reference/agnitio_get_meta-1), [version metadata](https://docs.lightcast.io/lightcast-api/reference/agnitio_get_version-1), [hierarchies](https://docs.lightcast.io/lightcast-api/reference/agnitio_get_version_dimension-1), [dimension search](https://docs.lightcast.io/lightcast-api/reference/agnitio_get_dimension_search-1), and [query schema](https://docs.lightcast.io/lightcast-api/reference/agnitio_post_version-1).
