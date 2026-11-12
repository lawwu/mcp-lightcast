# Choose the right tool

Start with metadata when you need to discover valid fields, models, datasets, or taxonomy versions. Use returned IDs in follow-up calls.

## Skills and titles

| Your question | Tool |
| --- | --- |
| What is the standardized ID for this skill? | `search_skills` |
| What does this skill record contain? | `get_skill_details` |
| Which skills are explicitly mentioned in this text? | `extract_skills_from_text` |
| Which skills are related to this one? | `get_related_skills` |
| What is the standardized job title? | `normalize_job_title` |
| What titles match this phrase? | `search_job_titles` |

Skills search uses **type IDs**: `ST1` for specialized skills, `ST2` for common skills, and `ST3` for certifications. The current search endpoint does not support category filters.

Extraction finds mentions in text. It does not tell you everything a person with that job title should know. For inferred occupational associations, use the title-to-skills workflow.

## Relationships and careers

| Your question | Tool |
| --- | --- |
| Which LOT occupations fit a title and description? | `classify_occupation` |
| How do IDs map between taxonomies? | `list_taxonomy_mappings`, then `map_taxonomy_concepts` |
| Which skills are associated with this occupation? | `query_similarity` with `lotspecocc-skill` |
| Which occupations are similar? | `query_similarity` with `soc`, `onet`, or `lotocc` |
| What could be a next career step? | `get_career_next_steps` |
| What is the skill gap between two occupations? | `get_career_skill_gap` |

The Similarity API returns model scores and can return warnings when evidence is insufficient. Its scores are model outputs, not guarantees of an individual’s career outcome. See [Lightcast’s model documentation](https://docs.lightcast.io/lightcast-api/reference/overview-similarity).

## Labor-market data

| Your question | Tool |
| --- | --- |
| Which US postings match these filters? | `search_job_postings` |
| How many matching postings exist? | `get_posting_statistics` |
| What are the top skills or employers? | `get_posting_rankings` |
| What does an occupation’s salary or demand look like? | `get_occupation_benchmark` |

Use `get_postings_metadata` to discover supported filters and metrics. Every posting query requires `filters.when`: either `"active"` or a `{ "start": "2026-10", "end": "2026-10" }` range. Benchmark IDs must be LOT occupations or specialized occupations; SOC codes do not belong in this endpoint.

## Combined workflows

`normalize_title_and_get_skills` performs normalization, LOT classification, and Similarity lookup. It deduplicates skills by ID, keeps source occupation IDs, and reports partial failures in `workflow_metadata`.

`analyze_job_posting_skills` normalizes a title and extracts explicit mentions from the title and description. Each combined skill keeps its ID and text source.

`normalize_title_and_extract_skills` uses Classification for both normalization and extraction. It preserves warnings and uses an active classifier release.

See the [complete input schemas](reference/tools.md) for all 37 tools.

## Core LMI

Use `list_core_lmi_datasets` → `get_core_lmi_versions` → `get_core_lmi_metadata` → `get_core_lmi_dimension` → `query_core_lmi` to move from account access to a reproducible data query. [Core LMI examples](core-lmi.md) cover employment, annual earnings, regional industry analysis, and education completions, plus the observed pagination and cost-of-living limitations.
