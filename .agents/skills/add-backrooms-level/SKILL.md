---
name: add-backrooms-level
description: Research and add or complete a Backrooms Wikidot level in Backrooms Archive. Use when the user asks to add, import, collect, or complete a Backrooms level, including replacing an existing placeholder with verified content.
---

# Add Backrooms Level

## Purpose

Import one requested Backrooms level into Backrooms Archive using the English Backrooms Wikidot as the canonical source.

Produce a structured Traditional Chinese article, preserve important source information, process appropriately licensed images, and maintain navigable level connections.

This skill runs during development. It does not require a runtime LLM API.

## 1. Read Project Rules

Before beginning:

1. Read the repository's `AGENTS.md`.
2. Inspect the current level data schema and existing examples.
3. Check whether `scripts/build_index.py` and `scripts/validate.py` exist and work.
4. Identify the requested level ID.

Follow `AGENTS.md` whenever this skill does not specify a more detailed procedure. Do not override project-wide rules.

## 2. Scope and Existing Data

Import only the level explicitly requested by the user.

For example, when asked to add Level 94:

- Research and complete Level 94.
- Create placeholders for verified, supported exit destinations that are not yet recorded.
- Do not retrieve the complete articles of those destinations.
- Do not recursively follow their connections.

Before importing, inspect:

`data/levels/level-{id}/index.json`

Handle the existing state as follows:

| Existing state | Action |
|---|---|
| No directory | Create a new complete level |
| Placeholder | Upgrade it to complete |
| Complete | Do not overwrite without explicit authorization |
| Invalid or conflicting data | Stop the affected operation and report the issue |

Preserve unrelated levels and files.

## 3. Locate and Verify the Source

Use only:

`https://backrooms-wiki.wikidot.com/`

For an ordinary numbered level, the expected URL pattern is:

`https://backrooms-wiki.wikidot.com/level-{id}`

Treat this pattern as a candidate, not proof that the page exists.

### Procedure

1. Locate the requested article on Backrooms Wikidot.
2. Verify that the page exists and corresponds to the requested level.
3. Confirm the canonical URL and article title.
4. Read the article's actual content, not only a search-result snippet.
5. Inspect relevant source links and media information when necessary.

If the page is unavailable, inaccessible, or ambiguous, do not invent its content.

Report the problem and stop the import when the canonical article cannot be verified.

Do not substitute information from Fandom, other Backrooms communities, or unrelated websites.

## 4. Extract Article Structure

Analyze the original article before generating JSON.

Identify:

- Article title and level identifier.
- Main sections and their order.
- Environmental descriptions.
- Survival or safety information, when present.
- Entities and hazards, when present.
- Exploration logs, interviews, and narrative material.
- Important images.
- Entrances and exits.
- Any unusual article structure that affects comprehension.

Do not assume every level uses the same headings.

### Section handling

Preserve the original article's major section order.

Use the existing schema:

```json
{
  "title": "描述",
  "blocks": [
    {
      "type": "text",
      "content": "繁體中文整理內容"
    }
  ]
}
```

Use multiple blocks when necessary to preserve the order of text and images.

Do not introduce unsupported block types.

If the source contains essential structures that cannot be represented accurately, report the limitation rather than silently discarding important information.

## 5. Write Traditional Chinese Content

Write all article content in natural Traditional Chinese (`zh-TW`).

### Summarization rules

- Produce detailed summaries, not short abstracts.
- Preserve important facts, descriptions, events, and narrative developments.
- Preserve the meaning and chronology of exploration logs.
- Maintain the atmosphere of the source without inventing new lore.
- Preserve important proper nouns and original level identifiers.
- Keep the distinction between confirmed facts, rumors, and unreliable narrators.
- Do not turn uncertain source claims into definitive statements.
- Do not reproduce the entire original article verbatim.

### Narrative content

For logs, interviews, and stories:

- Retain the sequence of significant events.
- Preserve relevant character actions and discoveries.
- Summarize dialogue when appropriate.
- Avoid inventing dialogue or outcomes.
- Preserve ambiguity when it is important to the story.

If a section cannot be summarized faithfully, explicitly identify the limitation.

## 6. Process Images

Important images may be included when their licensing and redistribution conditions permit.

### Procedure

1. Identify images that materially contribute to understanding the level.
2. Locate the original image source and available attribution information.
3. Verify the applicable license and redistribution conditions.
4. Download only images whose use is permitted.
5. Store them under the level's `images/` directory.
6. Record the image source and license in the corresponding JSON block.

Example:

```json
{
  "type": "image",
  "src": "images/pool.jpg",
  "caption": "圖片的繁體中文說明",
  "source_url": "https://example.com/original-image",
  "license": "Verified license information"
}
```

The URL above is a schema example, not an authorized image source.

### Restrictions

- Never fabricate license information.
- Do not assume that every image shares the article's license.
- Do not download images when permission cannot be established.
- Do not use unrelated replacement images.
- Preserve required creator attribution and license links.
- Do not alter an image in a way that misrepresents canonical source material.

If an image cannot be included, omit its local image block and report the omission. Preserve an appropriate source reference when useful.

## 7. Extract Entrances and Exits

Read the article's actual entrance and exit descriptions.

Create structured connection records only when supported by the source.

Example:

```json
{
  "target": "95",
  "description": "依來源整理的出口條件"
}
```

### Connection rules

- Preserve the direction of every connection.
- Never infer reverse connections.
- Do not invent destinations.
- Preserve conditions required to access a destination.
- Use consistent destination identifiers.
- Do not interpret every mention of another level as an entrance or exit.

### Unresolved destinations

Some exits may lead to unnamed, ambiguous, or nonstandard locations.

When a destination cannot be represented using the supported schema:

- Preserve the relevant description in the article.
- Do not invent a numeric level ID.
- Do not create a misleading placeholder.
- Report the unresolved connection.

Do not modify the global schema without explicit authorization.

## 8. Prepare Level Files

Create or update:

`data/levels/level-{id}/index.json`

Use the schema defined in `AGENTS.md`.

For complete levels, include:

- `id`
- `status`
- `name`
- `language`
- `source_url`
- `sections`
- `entrances`
- `exits`

Use `"status": "complete"` only after the content has been sufficiently researched and validated.

Ensure that every local image path resolves relative to the level directory.

Keep the JSON syntactically valid and consistently formatted.

## 9. Create Destination Placeholders

For each verified exit destination with a supported identifier:

1. Check whether the destination already exists.
2. If it exists, leave it unchanged.
3. Otherwise, create its directory.
4. Create a minimal placeholder `index.json`.

Example:

```json
{
  "id": "95",
  "status": "placeholder"
}
```

Do not create an `images/` directory for a placeholder unless it is needed later.

Do not fetch or summarize the placeholder's source article.

Do not create placeholders for unsupported or ambiguous destinations.

## 10. Generate Index and Validate

After preparing the new data, run:

```bash
python scripts/validate.py --source-only
python scripts/build_index.py
python scripts/validate.py
```

`--source-only` checks the original level data without requiring an index. The builder
repeats that check before writing `data/index.json`. Default validation checks the source
data and requires the index to match it, including all complete and placeholder levels.
Stop at the first failed command.

Validation must cover:

- JSON syntax.
- Required fields.
- Valid status values.
- Directory and ID consistency.
- Unique level identifiers.
- Supported content block types.
- Existing local image files.
- Image source and licensing metadata.
- Valid connection records.
- Existing destination records for supported exits.

### Failure handling

If a required script is missing or fails:

- Do not claim successful completion.
- Report the exact problem.
- Do not bypass validation by manually editing the generated index.
- Do not modify validation rules merely to make invalid data pass.

Avoid leaving partially written or corrupted files. Prepare and verify changes before replacing existing data where practical.

## 11. Verify Website Integration

When the frontend is available, verify that:

1. The imported level appears in the homepage directory.
2. The level article opens successfully.
3. Sections appear in the intended order.
4. Images load and display attribution.
5. Exit links navigate to the correct destinations.
6. Placeholder destinations display the expected message.
7. Existing levels remain accessible.

Do not create a separate HTML page for the new level.

Do not modify frontend files as part of ordinary level import.

If website integration cannot be tested, report that limitation.

## 12. Report Results

After execution, provide a concise report in Traditional Chinese.

Include:

- Requested level ID and title.
- Verified Wikidot source URL.
- Created or updated files.
- Number of imported sections and images.
- New placeholder destinations.
- Validation results.
- Any omitted images, unresolved connections, or other limitations.

Do not report a level as successfully imported if required validation failed.

## 13. Completion Criteria

The task is complete only when:

- The canonical Wikidot article was verified.
- The requested level has valid complete data.
- Important source content was accurately summarized.
- Included images have appropriate source and licensing information.
- Supported exit destinations have records.
- The global index was regenerated.
- Validation passed.
- Website integration was verified when available.
- The final report identifies any remaining limitations.

Never invent missing Backrooms lore to satisfy these criteria.
