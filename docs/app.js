async function loadPapers() {
  const res = await fetch('data/papers.json', { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to load papers.json: ${res.status}`);
  return await res.json();
}

function escapeHtml(s) {
  return (s || '')
    .toString()
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function renderMaybeLong(title, maxLen = 140) {
  return (data, type, row) => {
    const s = (data || '').toString();
    if (type !== 'display') return s;
    const trimmed = s.trim();
    if (!trimmed) return '';
    if (trimmed.length <= maxLen) return escapeHtml(trimmed);
    const short = escapeHtml(trimmed.slice(0, maxLen)) + '…';
    const full = escapeHtml(trimmed);
    return `${short} <a href="#" class="cell-more" data-title="${escapeHtml(title)}" data-full="${full}">Show more</a>`;
  };
}

function makeColumns(sample) {
  const cols = [];

  const pushIf = (key, title, render) => {
    if (Object.prototype.hasOwnProperty.call(sample, key)) {
      cols.push({ data: key, title, render });
    }
  };

  pushIf('Paper_ID', 'Paper_ID');
  pushIf('Title', 'Title', renderMaybeLong('Title', 160));
  pushIf('DOI', 'DOI', (data, type, row) => {
    const doi = (data || '').toString().trim();
    const url = (row.DOI_URL || '').toString().trim();
    if (!doi) return '';
    if (type !== 'display') return doi;
    if (!url) return escapeHtml(doi);
    return `<a href="${url}" target="_blank" rel="noopener">${escapeHtml(doi)}</a>`;
  });

  pushIf('Year', 'Year');
  pushIf('Country_norm', 'Country');
  pushIf('Crops_norm', 'Crops');
  pushIf('Workflow_Groups_str', 'Workflow group');

  pushIf('DataUsed_MZ', 'Data used for MZ', renderMaybeLong('Data used for MZ', 140));

  // Use explanation text for methods display
  pushIf('Methods_Explanation', 'Methods (workflow explanations)', renderMaybeLong('Methods (workflow explanations)', 180));

  pushIf('Validation_Tier_str', 'Validation tier');
  pushIf('Validation Description', 'Validation description', renderMaybeLong('Validation description', 180));

  // Abstract (snippet; can be increased later)
  pushIf('Abstract', 'Abstract', renderMaybeLong('Abstract', 180));

  return cols;
}

function uniqSorted(arr) {
  const s = new Set();
  for (const v of arr) {
    const t = (v || '').toString().trim();
    if (t) s.add(t);
  }
  return Array.from(s).sort((a, b) => a.localeCompare(b));
}

function splitSemi(v) {
  const s = (v || '').toString();
  return s
    .split(/[,;]+/)
    .map((x) => x.trim())
    .filter((x) => x.length > 0);
}

function setOptions(sel, values) {
  sel.innerHTML = '';
  for (const v of values) {
    const opt = document.createElement('option');
    opt.value = v;
    opt.textContent = v;
    sel.appendChild(opt);
  }
}

function getSelectedValues(sel) {
  return Array.from(sel.selectedOptions).map((o) => o.value);
}

async function main() {
  const data = await loadPapers();
  if (!Array.isArray(data) || data.length === 0) {
    document.getElementById('meta').innerHTML = 'No records found in data/papers.json';
    return;
  }

  const columns = makeColumns(data[0]);

  const tableEl = document.getElementById('papers');

  // Build header automatically for DataTables 2
  const thead = document.createElement('thead');
  const tr = document.createElement('tr');
  for (const c of columns) {
    const th = document.createElement('th');
    th.textContent = c.title;
    tr.appendChild(th);
  }
  thead.appendChild(tr);
  tableEl.appendChild(thead);

  const dt = new DataTable('#papers', {
    data,
    columns,
    pageLength: 25,
    scrollX: true,
  });

  const resultCount = document.getElementById('result-count');
  const yearSel = document.getElementById('f-year');
  const countrySel = document.getElementById('f-country');
  const cropsSel = document.getElementById('f-crops');
  const workflowsSel = document.getElementById('f-workflows');
  const validationSel = document.getElementById('f-validation');
  const dataUsedSel = document.getElementById('f-dataused');

  setOptions(yearSel, uniqSorted(data.map((r) => r.Year).filter((x) => x != null)).map((x) => x.toString()));
  setOptions(countrySel, uniqSorted(data.map((r) => r.Country_norm)));

  // Distinct crop tokens
  const cropTokens = [];
  for (const r of data) cropTokens.push(...splitSemi(r.Crops_norm));
  setOptions(cropsSel, uniqSorted(cropTokens));

  // Distinct workflow groups
  const wfTokens = [];
  for (const r of data) wfTokens.push(...splitSemi(r.Workflow_Groups_str));
  setOptions(workflowsSel, uniqSorted(wfTokens));

  // Validation tier
  const valTokens = [];
  for (const r of data) valTokens.push(...splitSemi(r.Validation_Tier_str));
  setOptions(validationSel, uniqSorted(valTokens));

  // Data used for MZ (distinct classes)
  const duTokens = [];
  for (const r of data) duTokens.push(...splitSemi(r.DataUsed_MZ));
  setOptions(dataUsedSel, uniqSorted(duTokens));

  // Enhance selects into searchable combo boxes
  $('#f-year, #f-country, #f-crops, #f-workflows, #f-validation, #f-dataused').select2({
    theme: 'bootstrap-5',
    width: '100%',
    closeOnSelect: false,
    placeholder: 'Any',
  });

  function applyFilters() {
    const years = new Set(getSelectedValues(yearSel));
    const countries = new Set(getSelectedValues(countrySel));
    const crops = new Set(getSelectedValues(cropsSel));
    const wfs = new Set(getSelectedValues(workflowsSel));
    const vals = new Set(getSelectedValues(validationSel));
    const dus = new Set(getSelectedValues(dataUsedSel));

    const filtered = data.filter((r) => {
      if (years.size && !years.has((r.Year ?? '').toString())) return false;
      if (countries.size && !countries.has((r.Country_norm ?? '').toString())) return false;

      if (crops.size) {
        const tokens = splitSemi(r.Crops_norm);
        let ok = false;
        for (const t of tokens) if (crops.has(t)) ok = true;
        if (!ok) return false;
      }

      if (wfs.size) {
        const tokens = splitSemi(r.Workflow_Groups_str);
        let ok = false;
        for (const t of tokens) if (wfs.has(t)) ok = true;
        if (!ok) return false;
      }

      if (vals.size) {
        const tokens = splitSemi(r.Validation_Tier_str);
        let ok = false;
        for (const t of tokens) if (vals.has(t)) ok = true;
        if (!ok) return false;
      }

      if (dus.size) {
        const tokens = splitSemi(r.DataUsed_MZ);
        let ok = false;
        for (const t of tokens) if (dus.has(t)) ok = true;
        if (!ok) return false;
      }

      return true;
    });

    dt.clear();
    dt.rows.add(filtered);
    dt.draw();
    resultCount.textContent = `${filtered.length} / ${data.length} papers`;
  }

  $('#f-year, #f-country, #f-crops, #f-workflows, #f-validation, #f-dataused').on('change', applyFilters);
  applyFilters();

  document.getElementById('clear-filters').addEventListener('click', () => {
    $('#f-year, #f-country, #f-crops, #f-workflows, #f-validation, #f-dataused').val(null).trigger('change');
  });

  // Show-more modal
  const modalEl = document.getElementById('cellModal');
  const modal = new bootstrap.Modal(modalEl);
  document.addEventListener('click', (ev) => {
    const a = ev.target.closest('a.cell-more');
    if (!a) return;
    ev.preventDefault();
    document.getElementById('cellModalTitle').textContent = a.dataset.title || 'Details';
    document.getElementById('cellModalBody').textContent = a.dataset.full || '';
    modal.show();
  });

}

main().catch((e) => {
  console.error(e);
  document.getElementById('meta').innerHTML = `Error: ${e.message}`;
});
