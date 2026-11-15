# Backrooms Archive — starter project

A small, data-driven level browser. The archive starts with an empty catalog.

## Run

From this folder:

```sh
python scripts/validate.py --source-only
python scripts/build_index.py
python scripts/validate.py
python -m http.server 8000
```

Open `http://localhost:8000`. A local server is needed because the browser loads JSON with `fetch`.

## Add a level

Follow `.agents/skills/add-backrooms-level/SKILL.md`. Verify the source against the [Backrooms Wikidot](https://backrooms-wiki.wikidot.com/) and save the record as `data/levels/level-{id}/index.json`. Run the three validation and build commands above in order, stopping if any fails.

## Layout

```text
AGENTS.md
README.md
.agents/skills/add-backrooms-level/SKILL.md
index.html
css/style.css
js/app.js
data/index.json
data/levels/
scripts/build_index.py
scripts/validate.py
assets/images/.gitkeep
```
