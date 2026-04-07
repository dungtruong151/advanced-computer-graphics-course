/**
 * app.js - Language switching and rendering.
 */

/** TOC config: [sectionId, i18nTitleKey, badgeType] */
const TOC_ENTRIES = [
  ['s1',  's1_title',  'theory'],
  ['s2',  's2_title',  'theory'],
  ['s3',  's3_title',  'theory'],
  ['s4',  's4_title',  'theory'],
  ['s5',  's5_title',  'theory'],
  ['s6',  's6_title',  'theory'],
  ['s7',  's7_title',  'theory'],
  ['s8',  's8_title',  'practice'],
  ['s9',  's9_title',  'practice'],
  ['s10', 's10_title', 'practice'],
];

/** Render table of contents */
function renderTOC() {
  const grid = document.getElementById('toc-grid');
  grid.innerHTML = TOC_ENTRIES.map(([id, key, badge]) => {
    const badgeCls = badge === 'theory' ? 'badge-theory' : 'badge-practice';
    const badgeLabel = badge === 'theory' ? 'LT' : 'TH';
    return `<a href="#${id}"><span class="badge ${badgeCls}">${badgeLabel}</span>${t(key)}</a>`;
  }).join('');
}

/** Update all data-i18n elements in the static HTML shell */
function updateStaticI18N() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    el.innerHTML = t(key);
  });
}

/** Full render */
function render() {
  updateStaticI18N();
  renderTOC();
  document.getElementById('content').innerHTML = buildSections();
}

/** Switch language */
function setLang(lang) {
  currentLang = lang;
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-lang-btn]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.langBtn === lang);
  });
  render();
}

/* --- Init --- */
document.querySelectorAll('[data-lang-btn]').forEach(btn => {
  btn.addEventListener('click', () => setLang(btn.dataset.langBtn));
});

render();
