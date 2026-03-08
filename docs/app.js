async function loadPapers() {
  const res = await fetch('data/papers.json', { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to load papers.json: ${res.status}`);
  return await res.json();
}

function makeColumns(sample) {
  // Minimal, reviewer-friendly default columns.
  // Additional fields remain searchable and visible via JSON/CSV export.
  const cols = [];

  const pushIf = (key, title, render) => {
    if (Object.prototype.hasOwnProperty.call(sample, key)) {
      cols.push({ data: key, title, render });
    }
  };

  pushIf('Paper_ID', 'Paper_ID');
  pushIf('Year', 'Year');
  pushIf('Country', 'Country');
  pushIf('Crops', 'Crops');
  pushIf('ManagementFocus', 'ManagementFocus');
  pushIf('Workflows', 'Workflows');
  pushIf('VI_Media', 'VI_Media');
  pushIf('Methods', 'Methods');
  pushIf('Validation-Code', 'Validation-Code');
  pushIf('Final_Decision', 'Final_Decision');
  pushIf('Score', 'Score');

  // Title
  pushIf('Title', 'Title');

  // DOI link
  pushIf('DOI', 'DOI', (data, type, row) => {
    const doi = (data || '').toString().trim();
    const url = (row.DOI_URL || '').toString().trim();
    if (!doi) return '';
    if (!url) return doi;
    return `<a href="${url}" target="_blank" rel="noopener">${doi}</a>`;
  });

  return cols;
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

  new DataTable('#papers', {
    data,
    columns,
    pageLength: 25,
    scrollX: true,
    dom: 'Pfrtip',
    searchPanes: {
      cascadePanes: true,
      viewTotal: true,
    },
    columnDefs: [
      { searchPanes: { show: true }, targets: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] },
    ],
  });
}

main().catch((e) => {
  console.error(e);
  document.getElementById('meta').innerHTML = `Error: ${e.message}`;
});
