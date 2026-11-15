const main = document.querySelector('#content');
document.querySelector('.skip-link').addEventListener('click', event => {
  event.preventDefault();
  main.focus();
});
let entries = [];
let ready = false;
let requestId = 0;

function element(parent, tag, value, className) {
  const node = document.createElement(tag);
  if (value !== undefined) node.textContent = String(value);
  if (className) node.className = className;
  parent.append(node);
  return node;
}

function safeUrl(value) {
  if (typeof value !== 'string') return null;
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : null;
  } catch { return null; }
}

function pathFor(entry) {
  const expected = `levels/level-${entry.id}/index.json`;
  return entry.path === expected ? `data/${expected}` : null;
}

function route() {
  if (!location.hash || location.hash === '#/' || location.hash === '#') return { page: 'home' };
  const match = /^#\/level\/([0-9]+)$/.exec(location.hash);
  return match ? { page: 'level', id: match[1] } : { page: 'invalid' };
}

function backLink() {
  const link = element(main, 'a', '← 返回層級目錄', 'back');
  link.href = '#/';
}

function errorPage(title, detail) {
  main.replaceChildren();
  backLink();
  element(main, 'h1', title);
  element(main, 'p', detail, 'notice');
}

function home() {
  main.replaceChildren();
  element(main, 'p', 'LEVEL DIRECTORY / 層級目錄', 'eyebrow');
  element(main, 'h1', 'Backrooms Archive');
  element(main, 'p', '探索已收錄的後室層級。完整條目整理自 Backrooms Wikidot；尚未收錄的目的地保留導覽入口，等待日後補全。', 'intro');
  const search = element(main, 'section', undefined, 'panel search-panel');
  const label = element(search, 'label', '搜尋層級 ID 或名稱');
  label.htmlFor = 'level-search';
  const input = element(search, 'input');
  input.id = 'level-search';
  input.type = 'search';
  input.placeholder = '例如：37、Sublimity';
  const count = element(search, 'p', '', 'count');
  const directory = element(main, 'div', undefined, 'directory');
  directory.setAttribute('aria-label', '層級目錄');
  function filter() {
    const query = input.value.trim().toLocaleLowerCase();
    const found = entries.filter(item => item.id.includes(query) || (item.name || '').toLocaleLowerCase().includes(query));
    count.textContent = `顯示 ${found.length} / ${entries.length} 個層級`;
    directory.replaceChildren();
    if (!found.length) element(directory, 'p', '找不到符合的層級。', 'notice');
    for (const item of found) {
      const card = element(directory, 'a', undefined, 'level-card');
      card.href = `#/level/${item.id}`;
      const name = element(card, 'span');
      element(name, 'strong', `Level ${item.id}${item.name ? ` — ${item.name}` : ''}`);
      element(name, 'small', item.status === 'complete' ? '可閱讀完整條目' : '目的地佔位頁');
      element(card, 'span', item.status === 'complete' ? '已收錄' : '尚未收錄', `status ${item.status}`);
    }
  }
  input.addEventListener('input', filter);
  filter();
}

function renderImage(parent, block, dataPath) {
  const figure = element(parent, 'figure', undefined, 'figure');
  const valid = typeof block.src === 'string' && /^images\/[a-zA-Z0-9._/-]+$/.test(block.src) && !block.src.split('/').includes('..');
  if (valid) {
    const image = element(figure, 'img');
    image.src = new URL(block.src, new URL('./', new URL(dataPath, location.href))).href;
    image.alt = typeof block.caption === 'string' ? block.caption : '層級圖片';
    image.loading = 'lazy';
    image.addEventListener('error', () => {
      image.remove();
      element(figure, 'p', '圖片無法載入，請參閱原始來源。', 'notice');
    }, { once: true });
  } else element(figure, 'p', '圖片路徑無效，無法顯示。', 'notice');
  const caption = element(figure, 'figcaption');
  element(caption, 'p', typeof block.caption === 'string' ? block.caption : '未提供圖片說明');
  const source = safeUrl(block.source_url);
  if (source) {
    const link = element(caption, 'a', '查看原始圖片');
    link.href = source;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  } else element(caption, 'p', '原始圖片連結無效。');
  element(caption, 'p', `授權：${typeof block.license === 'string' ? block.license : '未提供'}`, 'meta');
}

function connections(parent, title, records) {
  const panel = element(parent, 'section', undefined, 'connection-panel');
  element(panel, 'h2', title);
  if (!Array.isArray(records)) { element(panel, 'p', '出入口資料格式錯誤。', 'notice'); return; }
  if (!records.length) { element(panel, 'p', '未記載相關路徑。'); return; }
  const list = element(panel, 'ul');
  for (const record of records) {
    const item = element(list, 'li');
    if (!record || typeof record !== 'object') { element(item, 'span', '無法顯示此筆路徑資料。'); continue; }
    element(item, 'span', typeof record.description === 'string' ? record.description : '未提供路徑說明。');
    if (typeof record.target === 'string' && entries.some(entry => entry.id === record.target)) {
      const link = element(item, 'a', `前往 Level ${record.target} →`);
      link.href = `#/level/${record.target}`;
    }
  }
}

function levelPage(level, entry) {
  main.replaceChildren();
  backLink();
  if (!level || typeof level !== 'object' || level.id !== entry.id || level.status !== entry.status) {
    element(main, 'h1', '層級資料格式錯誤');
    element(main, 'p', '層級 ID 或狀態與目錄不符。', 'notice');
    return;
  }
  const header = element(main, 'header', undefined, 'article-head');
  element(header, 'p', `LEVEL ${entry.id} / 檔案紀錄`, 'eyebrow');
  if (entry.status === 'placeholder') {
    element(header, 'h1', `Level ${entry.id}`);
    element(header, 'span', '尚未收錄', 'status placeholder');
    element(main, 'p', '此層級尚未收錄', 'notice');
    return;
  }
  if (typeof level.name !== 'string' || !Array.isArray(level.sections)) {
    element(header, 'h1', '層級資料格式錯誤');
    element(main, 'p', '文章缺少名稱或章節。', 'notice');
    return;
  }
  element(header, 'h1', `Level ${entry.id} — ${level.name}`);
  element(header, 'span', '已收錄', 'status complete');
  const sections = element(main, 'div', undefined, 'sections');
  for (const section of level.sections) {
    const box = element(sections, 'section', undefined, 'section');
    if (!section || typeof section.title !== 'string' || !Array.isArray(section.blocks)) {
      element(box, 'p', '章節資料格式錯誤。', 'notice');
      continue;
    }
    element(box, 'h2', section.title);
    for (const block of section.blocks) {
      if (!block || typeof block !== 'object') { element(box, 'p', '不支援的內容區塊。', 'notice'); continue; }
      if (block.type === 'text' && typeof block.content === 'string') element(box, 'p', block.content);
      else if (block.type === 'image') renderImage(box, block, `data/${entry.path}`);
      else element(box, 'p', `不支援的內容區塊：${typeof block.type === 'string' ? block.type : '未知類型'}`, 'notice');
    }
  }
  const grid = element(main, 'div', undefined, 'connection-grid');
  connections(grid, '入口', level.entrances);
  connections(grid, '出口', level.exits);
  const source = safeUrl(level.source_url);
  if (source && new URL(source).hostname === 'backrooms-wiki.wikidot.com') {
    const paragraph = element(main, 'p', undefined, 'source');
    const link = element(paragraph, 'a', '閱讀 Backrooms Wikidot 原文 ↗');
    link.href = source;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  }
}

async function showRoute() {
  const currentRequest = ++requestId;
  if (!ready) return;
  const selected = route();
  if (selected.page === 'home') { home(); return; }
  if (selected.page === 'invalid') { errorPage('無法辨識的頁面', '請使用層級目錄開啟條目。'); return; }
  const entry = entries.find(item => item.id === selected.id);
  if (!entry) { errorPage('找不到此層級', `Level ${selected.id} 尚未列入目錄。`); return; }
  main.replaceChildren();
  element(main, 'p', '正在讀取層級資料……');
  try {
    const response = await fetch(pathFor(entry));
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (currentRequest === requestId) levelPage(data, entry);
  } catch (error) {
    if (currentRequest === requestId) errorPage('無法載入層級資料', `Level ${entry.id} 的資料讀取失敗：${error.message}`);
  }
}

async function start() {
  try {
    const response = await fetch('data/index.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const index = await response.json();
    if (!index || !Array.isArray(index.levels)) throw new Error('目錄格式錯誤');
    entries = index.levels.filter(item => item && typeof item.id === 'string' && /^[0-9]+$/.test(item.id) && ['complete', 'placeholder'].includes(item.status) && pathFor(item)).sort((a, b) => {
      const x = BigInt(a.id), y = BigInt(b.id);
      return x < y ? -1 : x > y ? 1 : a.id.localeCompare(b.id);
    });
    ready = true;
    showRoute();
  } catch (error) {
    main.replaceChildren();
    element(main, 'h1', '無法載入層級目錄');
    element(main, 'p', `請稍後重試。原因：${error.message}`, 'notice');
  }
}

window.addEventListener('hashchange', showRoute);
start();
