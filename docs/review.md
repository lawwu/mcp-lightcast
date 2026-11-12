# API compatibility review

**Reviewed November 12, 2026 · Version 0.3.0**

This review compared the implementation with Lightcast’s current reference and embedded OpenAPI definitions, then exercised the integration using real account credentials. The server exposes a focused subset of eight API families; it does not claim to implement every Lightcast endpoint.

## Original seven-family verification

The review account successfully authenticated to all seven families and completed representative data operations:

| API family | Verified operations |
| --- | --- |
| Skills | Search with type filter, detail, bulk retrieval, related skills, text extraction |
| Titles | Search, detail, bulk retrieval, normalization |
| Classification | Active releases, source types, LOT classification, skill extraction, title normalization, mapping discovery and application |
| Similarity | Skill similarity, SOC similarity, LOT specialized occupation → skills |
| Occupation Benchmark | LOT occupation taxonomy information and salary request |
| Career Pathways | Next-step occupations and occupation-to-occupation skill gaps |
| US Job Postings | Metadata, totals, skill rankings, search, posting details |

Metadata reported Skills **10.1**, Titles **5.64**, and classifier release **2026.11**. These are observed values, not hardcoded defaults. Access to a tested operation does not establish unlimited quota, access to every region, or every dataset. Benchmark and model warnings remain part of returned responses.

## Core LMI and MCP follow-up

The follow-up adds five Core LMI tools and tests actual data queries against three datasets on release 2026.4. **18 Core LMI checks passed**, including discovery, employment and earnings, distinct query pages, combined regions, location quotient, shift share, and education completions. The account catalog listed 52 datasets.

Live requests exposed ignored native offsets and page-sized `totalRows` values; bounded prefix retrieval now produces distinct pages. Cost-of-living metadata was accessible, but the documented data-query forms returned HTTP 400. This limitation is recorded in the [Core LMI guide](core-lmi.md).

The [MCP review](mcp-review.md) documents the upgrade to the 2026-07-28 protocol with legacy compatibility, strict arguments, actionable errors, and HTTP Origin/Host protection.

## Findings and repairs

| Priority | Finding | Repair |
| --- | --- | --- |
| High | Shared mutable OAuth scope could cross-contaminate concurrent requests | Tokens and refresh locks are separated by requested scope |
| High | Configuration loaded before `--env-file`; wheel relied on repository-only imports | Lazy settings ship inside the package; CLI loads environment before importing clients |
| High | Startup output could corrupt stdio MCP communication | Clean stdout; stderr logging; default stdio transport |
| High | Benchmarks and classification could return simulated success after API failures | Removed fabricated fallback results and speculative endpoint helpers |
| High | Job-posting tools called nonexistent methods or invented versioned routes | Implemented JPA `/postings`, `/totals`, and `/rankings/{facet}` with required time filters |
| High | Title detail/bulk tools accessed model fields that did not exist | Serialize validated title models with optional fields |
| High | The combined workflow extracted words from titles while claiming occupation skill mapping | Implemented real normalization → LOT classification → Similarity, with provenance and partial status |
| Medium | Titles normalized `latest` to an old pinned version | Preserve the documented `latest` alias |
| Medium | Classification release `2025.8` had expired | Discover active releases and select the newest numerically |
| Medium | Skills bulk retrieval used `/retrieve`; related-skill limit was ignored; filter used `type` | Use `/skills`, transmit `limit`, and send `typeIds` |
| Medium | Similarity thresholds were ignored and methods used unsupported endpoints | Use `/models/{model}` with `filter.minScore` and supported input types |
| Medium | No useful quota handling or rate spacing | Shared per-service spacing, bounded retries, reset headers, one-time 401 refresh |
| Medium | Skill IDs disappeared during workflow combination | Preserve IDs and deduplicate by ID with source provenance |
| Medium | Tests could contact the live API merely because `.env` existed | Offline network guard and explicit `--live` flag |
| Medium | CI targeted Python versions below the package minimum | Test Python 3.12, 3.13, and 3.14; use locked dependencies |
| Medium | Docker used an incorrect OAuth URL and a meaningless health check | Package-only runtime image, correct packaged defaults, no fake health assertion |
| Low | Package URLs, release notes, and setup instructions had stale placeholders | Correct project links, migration guide, generated tool reference, and automatic Pages build |

## Official sources

These are the primary contracts used during the review:

- [Skills search](https://docs.lightcast.io/lightcast-api/reference/skills_get_all_skills), [bulk retrieval](https://docs.lightcast.io/lightcast-api/reference/skills_post_versions_version_skills), and [related skills](https://docs.lightcast.io/lightcast-api/reference/skills_post_find_related_skills).
- [Titles versions](https://docs.lightcast.io/lightcast-api/reference/getversions), [normalization](https://docs.lightcast.io/lightcast-api/reference/normalize), and [title details](https://docs.lightcast.io/lightcast-api/reference/gettitlebyid).
- [Classification releases and expiry](https://docs.lightcast.io/lightcast-api/reference/classification_get_classifications), [LOT classification](https://docs.lightcast.io/lightcast-api/reference/classification_post_release_lot_classify), [normalization](https://docs.lightcast.io/lightcast-api/reference/classification_post_release_titles_normalize), and [mapping](https://docs.lightcast.io/lightcast-api/reference/classification_post_mapping_name).
- [Similarity mappings](https://docs.lightcast.io/lightcast-api/reference/post_models-model).
- [Occupation Benchmark dimensions](https://docs.lightcast.io/lightcast-api/reference/occupation_benchmark_post_dimension).
- [Career next steps](https://docs.lightcast.io/lightcast-api/reference/post_dimensions-dimension-nextstepjobs) and [skill gaps](https://docs.lightcast.io/lightcast-api/reference/post_dimensions-dimension-skillgap).
- [US posting search](https://docs.lightcast.io/lightcast-api/reference/jpa_post_postings), [totals](https://docs.lightcast.io/lightcast-api/reference/jpa_post_totals), and [rankings](https://docs.lightcast.io/lightcast-api/reference/jpa_post_rankings_facet).

## Verification scope

Offline tests assert HTTP paths and bodies, concurrency behavior, input constraints, error propagation, and actual MCP calls. The live runner checks operation availability using small requests through the MCP server. It does not compare all returned market data with independent ground truth or exercise every possible filter combination.

The updated suite completed **98 offline tests**, **32 existing live MCP tool checks**, and **18 Core LMI live checks**. Offline tests passed on Python 3.13 and 3.14. An isolated Python 3.12 wheel installation passed stdio and streamable HTTP connections with both the current and legacy protocols, 37-tool discovery, version reporting, and external environment-file loading. Browser checks covered the new Core LMI and MCP guides; the original site review also covered search, light/dark themes, and a 390-pixel mobile layout.

The docs build uses Zensical, is strict, and generates the reference from registered tool schemas. See [testing](testing.md) for repeatable commands and [migration](migration.md) for breaking contract corrections.
