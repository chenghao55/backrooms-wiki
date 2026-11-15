const list = document.querySelector('#levels');
const detail = document.querySelector('#detail');
let entries = [];

function setText(parent, tag, value) {
  const el = document.createElement(tag);
  el.textContent = value;
  parent.append(el);
  return el;
}

async function showLevel(id) {
  const entry = entries.find(item => item.id === id);
  if (!entry) return;
  detail.replaceChildren();
  try {
    const response = await fetch(entry.path);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const level = await response.json();
    setText(detail, 'h2', level.title || `Level ${level.number}`);
    setText(detail, 'span', level.status === 'verified' ? 'Verified' : 'Unsourced starter / draft').className = 'badge';
    setText(detail, 'p', level.summary || 'No verified description has been added.');
    setText(detail, 'h3', 'Exits');
    if (level.exits.length === 0) setText(detail, 'p', 'No verified exits have been added.').className = 'muted';
    else {
      const ul = document.createElement('ul');
      for (const exit of level.exits) {
        const li = setText(ul, 'li', `${exit.label}${exit.target_status === 'placeholder' ? ' (destination placeholder)' : ''}`);
        if (exit.target_id && entries.some(item => item.id === exit.target_id)) {
          const link = setText(li, 'a', ' → Open');
          link.href = `#${encodeURIComponent(exit.target_id)}`;
        }
      }
      detail.append(ul);
    }
    if (level.source_url) {
      const link = setText(detail, 'a', 'Wikidot source');
      link.href = level.source_url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    }
    for (const link of list.querySelectorAll('a')) link.setAttribute('aria-current', link.hash === `#${encodeURIComponent(id)}` ? 'page' : 'false');
  } catch (error) {
    setText(detail, 'p', `Could not load this level: ${error.message}`);
  }
}

async function start() {
  try {
    const response = await fetch('data/index.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    entries = (await response.json()).levels;
    list.replaceChildren();
    for (const item of entries) {
      const link = setText(list, 'a', item.title || `Level ${item.number}`);
      link.href = `#${encodeURIComponent(item.id)}`;
    }
    if (entries.length) showLevel(decodeURIComponent(location.hash.slice(1)) || entries[0].id);
    else setText(detail, 'p', 'No levels have been added yet.');
  } catch (error) {
    list.textContent = `Could not load index: ${error.message}`;
  }
}
window.addEventListener('hashchange', () => showLevel(decodeURIComponent(location.hash.slice(1))));
start();
