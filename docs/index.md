---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>
<div markdown>
<div class="eyebrow">MCP LIGHTCAST / DEVELOPER DOCUMENTATION</div>

# Labor-market data.<br><em>Within reach.</em>

<p class="lead">Give your AI tools a shared language for jobs, skills, and careers. Connect to Lightcast’s labor-market intelligence through one focused MCP server.</p>

<div class="hero-actions" markdown>
[Get connected →](getting-started.md){ .md-button .md-button--primary }
[Explore the tools](reference/tools.md){ .md-button }
</div>

Python 3.12+ · Local or HTTP · Open source

</div>
<div class="pipeline" role="img" aria-label="Illustrative workflow: normalize a job title, classify its occupation, and discover associated skills">
<div class="panel-top"><span>FROM TITLE TO CONTEXT</span><span class="status">● MCP CONNECTED</span></div>
<div class="step"><div class="step-label">01 / Your input</div><div class="step-value">“Sr. software engineer”</div></div>
<div class="arrow">↓ &nbsp; Normalize & classify</div>
<div class="step"><div class="step-label">02 / A common language</div><div class="step-value">Software Developer / Engineer</div></div>
<div class="arrow">↓ &nbsp; Discover associated skills</div>
<div class="step"><div class="step-label">03 / Structured intelligence</div><div class="pills"><span class="pill">Software development</span><span class="pill">Python</span><span class="pill">SQL</span></div></div>
<div class="caption">Illustrative workflow · Results depend on the model and your API access.</div>
</div>
</div>

<div class="stats">
<div><strong>37</strong><span>purposeful MCP tools</span></div>
<div><strong>8</strong><span>Lightcast API families</span></div>
<div><strong>1</strong><span>connection for your assistant</span></div>
</div>

## From a question to useful data

<div class="feature-grid" markdown>
<div class="feature" markdown>
<span class="number">01 / UNDERSTAND</span>

### Make language consistent

Search skills, standardize messy titles, and extract the skills explicitly mentioned in a job description.

[Explore taxonomy tools →](tool-guide.md#skills-and-titles)
</div>
<div class="feature" markdown>
<span class="number">02 / CONNECT</span>

### See how work relates

Map occupations, compare skills, and explore career transitions using Lightcast’s published models.

[Explore relationship tools →](tool-guide.md#relationships-and-careers)
</div>
<div class="feature" markdown>
<span class="number">03 / INVESTIGATE</span>

### Put demand in context

Explore employment, earnings, education, US job postings, and occupation benchmarks with explicit dataset provenance.

[Explore market tools →](tool-guide.md#labor-market-data)
</div>
</div>

## A small setup. A useful connection.

```bash
# From a checkout with your credentials in .env
uv sync
uv run mcp-lightcast --validate-config
uv run mcp-lightcast --transport stdio
```

Add the server to your MCP client, then ask something concrete: **“Extract the skills in this job description and find related skills.”**

<div class="callout" markdown>
**Built around the current API contracts.**

Scope-specific authentication, live version discovery, bounded retries, and honest partial results. The November 2026 review documents the changes, the official sources, and exactly what was tested.

[Read the compatibility review →](review.md)
</div>
