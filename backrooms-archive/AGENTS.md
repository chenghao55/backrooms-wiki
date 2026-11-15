# AGENTS.md — Backrooms Archive

## 1. Project Overview

Backrooms Archive is a static, data-driven, interactive wiki for exploring interconnected Backrooms levels.

The website is hosted on GitHub Pages. AI agents maintain its content during development; visitors do not interact with an LLM.

### Core principles

- All level information must originate from the official [Backrooms Wikidot](https://backrooms-wiki.wikidot.com/).
- Website content must be written in Traditional Chinese (`zh-TW`).
- Preserve the major structure and important details of source articles.
- Summarize and reorganize information rather than reproducing entire articles verbatim.
- Levels are connected through directed entrances and exits.
- Uncollected destination levels must remain navigable through placeholder pages.
- Adding a level must not require manually creating or editing HTML pages.
- Never fabricate canonical Backrooms information.

## 2. Project Structure

```text
backrooms-archive/
├── AGENTS.md
├── README.md
├── .agents/
│   └── skills/
│       └── add-backrooms-level/
│           └── SKILL.md
├── index.html
├── css/
│   └── style.css
├── js/
│   └── app.js
├── data/
│   ├── index.json
│   └── levels/
│       └── level-{id}/
│           ├── index.json
│           └── images/
└── scripts/
    ├── build_index.py
    └── validate.py
```

### Responsibilities

- `AGENTS.md`: Project-wide rules and architecture.
- `SKILL.md`: Workflow for researching and adding Backrooms levels.
- `index.html`: Main website entry point.
- `app.js`: Level rendering, routing, navigation, and search.
- `style.css`: Shared visual design.
- `data/levels/`: Source of truth for level content.
- `data/index.json`: Generated directory of all recorded levels.
- `build_index.py`: Generates the directory from level data.
- `validate.py`: Checks data consistency and file references.

The presence of a file in this structure does not imply that its functionality has already been implemented.

## 3. Level Data Schema

Each level must have its own directory:

`data/levels/level-{id}/`

The directory must contain an `index.json`.

### Complete level

```json
{
  "id": "37",
  "status": "complete",
  "name": "Sublimity",
  "language": "zh-TW",
  "source_url": "https://backrooms-wiki.wikidot.com/level-37",
  "sections": [
    {
      "title": "描述",
      "blocks": [
        {
          "type": "text",
          "content": "繁體中文整理內容"
        }
      ]
    }
  ],
  "entrances": [],
  "exits": []
}
```

This is a structural example, not verified article content.

### Placeholder level

```json
{
  "id": "95",
  "status": "placeholder"
}
```

Placeholder levels must not contain fabricated descriptions, entities, or connections.

### Required fields

For complete levels:

- `id`: Unique string identifier.
- `status`: `"complete"`.
- `name`: Source article title or level name.
- `language`: `"zh-TW"`.
- `source_url`: Original Wikidot article URL.
- `sections`: Ordered article sections.
- `entrances`: Structured entrance records.
- `exits`: Structured exit records.

For placeholders, only `id` and `status` are required.

Missing information must not be replaced with invented content.

## 4. Article Content Rules

### Source policy

Only Backrooms Wikidot may be used as a canonical source.

Do not mix content from Fandom, unofficial wikis, or fan interpretations.

If the source page is unavailable, ambiguous, or cannot be verified, report the issue rather than inventing content.

### Language and summarization

- Write in natural Traditional Chinese.
- Preserve important facts, events, descriptions, and narrative context.
- Maintain the original article's major section order.
- Preserve proper nouns and level identifiers.
- Do not invent missing information.
- Do not present AI interpretation as canonical information.

### Article sections

Use the `sections` array to preserve the article's organization.

Each section contains a `title` and an ordered `blocks` array.

Supported block types in v1:

- `text`
- `image`

Do not force all articles to contain identical sections.

Entrances and exits must also be extracted into structured connection fields for navigation.

Avoid duplicating their full descriptions unnecessarily.

## 5. Image Rules

Important images may be included when their use is permitted.

Each image block must contain:

```json
{
  "type": "image",
  "src": "images/example.jpg",
  "caption": "圖片說明",
  "source_url": "原始圖片來源",
  "license": "已確認的授權資訊"
}
```

Rules:

- Store downloaded images inside the corresponding level's `images/` directory.
- Use paths relative to the level directory.
- Verify image licensing before downloading or redistributing.
- Preserve required attribution and license information.
- If permission or licensing cannot be verified, omit the local image and retain an appropriate source reference.
- Never fabricate image credits or licensing terms.

The website must display required attribution and licensing information.

## 6. Navigation Rules

### Directed connections

Entrances and exits represent directed relationships.

For example:

```json
{
  "target": "95",
  "description": "依來源確認的出口條件"
}
```

An exit from Level 94 to Level 95 does not imply an exit from Level 95 to Level 94.

Never automatically generate reverse connections.

### Placeholder creation

When adding a complete level:

1. Extract verified exit destinations.
2. Check whether each destination already exists.
3. If it exists, preserve its existing data.
4. If it does not exist, create a placeholder directory and `index.json`.
5. Do not recursively retrieve destination articles.

A placeholder must be accessible through the same navigation system as a complete level.

The website should display:

「此層級尚未收錄」

When a placeholder is later completed, its existing links must remain valid.

### Unresolved destinations

Some Wikidot exits may lead to locations that are not ordinary numbered levels.

Do not invent a numeric identifier.

Preserve the destination description and source information. Create a placeholder only when a supported destination identifier can be established.

## 7. Index Management

`data/levels/` is the single source of truth.

`data/index.json` is generated data and must not be manually maintained.

The index generator must:

- Scan `data/levels/*/index.json`.
- Read each level's identifier, name, and status.
- Detect duplicate identifiers.
- Produce a deterministic index.
- Include both complete and placeholder levels.

The homepage must use the generated index to display the level directory.

It must support distinguishing complete and placeholder records.

## 8. Frontend Rules

The website must be a static application compatible with GitHub Pages.

### Required functionality

- Display a homepage listing recorded levels.
- Open individual level pages.
- Render ordered article sections and content blocks.
- Display important images with attribution.
- Display entrances and exits.
- Navigate to connected levels.
- Render placeholder pages without broken links.

### Design principles

- Maintain a consistent Backrooms-inspired atmosphere.
- Prioritize readability and clear navigation.
- Support desktop and mobile layouts.
- Use shared styles and reusable rendering functions.
- Do not generate separate HTML files for individual levels.

Adding ordinary level content should require data changes only.

## 9. Agent Responsibilities

### General rules

Before making changes:

1. Read this `AGENTS.md`.
2. Inspect the existing project structure.
3. Follow the established data schema.
4. Preserve unrelated files and existing functionality.

Do not silently overwrite existing complete levels.

Do not change the schema or frontend architecture merely to accommodate a single unusual article.

Report unsupported content structures instead.

### Skill invocation

When the user requests adding, importing, or completing a Backrooms level, follow:

`.agents/skills/add-backrooms-level/SKILL.md`

The Skill is responsible for:

- Finding the source article.
- Retrieving and analyzing its content.
- Producing Traditional Chinese summaries.
- Processing permitted images.
- Extracting entrance and exit relationships.
- Creating or updating level data.
- Creating destination placeholders.
- Running validation and index generation.
- Reporting the result.

Detailed retrieval procedures belong in `SKILL.md`, not this document.

### Modification boundaries

The level-import workflow should normally modify only:

- `data/levels/`
- Generated `data/index.json`

Do not modify frontend code, validation scripts, or project-wide rules unless the user explicitly requests a feature or architecture change.

## 10. Validation and Completion

After adding or modifying level data, run:

```bash
python scripts/validate.py --source-only
python scripts/build_index.py
python scripts/validate.py
```

`--source-only` checks the original level data without requiring `data/index.json`.
The builder repeats source validation before writing the index. Default validation checks
the source data and requires the index to match it. Stop at the first failed command.

Validation should check:

- Valid JSON syntax.
- Required fields and supported statuses.
- Consistency between directory names and level IDs.
- Duplicate identifiers.
- Supported content block types.
- Image file existence and required attribution.
- Valid connection records.
- Existence of placeholder or complete records for supported exit destinations.

When possible, verify the website locally before reporting completion.

If any required validation fails, do not report the task as successfully completed.

## 11. Out of Scope for v1

The following features are not required for the first version:

- Runtime LLM API integration.
- Automatic recursive expansion of connected levels.
- Interactive level relationship graphs.
- User accounts or server-side databases.
- Automatic background crawling.
- Full reproduction of Wikidot's original layout.

These features may be considered in future versions, but must not be introduced without an explicit decision.

## 12. Definition of Done

A level-import task is complete only when:

1. The canonical source has been verified.
2. The level JSON follows the schema.
3. Important article information has been accurately summarized.
4. Supported exit destinations have valid records.
5. Required image attribution is present.
6. The generated directory is updated.
7. Validation passes.
8. The level can be opened through the website.
9. The agent reports created or modified files and any unresolved issues.
