document.addEventListener('DOMContentLoaded', function () {
  const container = document.querySelector('.grid__item');
  if (!container) return;

  const header = container.querySelector('.books__header');
  const emptyMessage = document.getElementById('books-empty-message');

  // Collect row/detail pairs
  function getBookPairs() {
    const pairs = [];
    const rows = container.querySelectorAll('.books__row');
    rows.forEach(function (row) {
      const chevron = row.querySelector('.books__chevron');
      const detailId = chevron ? chevron.dataset.detail : null;
      const detail = detailId ? document.getElementById(detailId) : null;
      pairs.push({ row: row, detail: detail });
    });
    return pairs;
  }

  // --- Sorting ---
  let currentSort = null;
  let sortAsc = true;

  const sortables = header.querySelectorAll('.books__sortable');
  sortables.forEach(function (el) {
    el.addEventListener('click', function () {
      const sortKey = el.dataset.sort;
      if (currentSort === sortKey) {
        sortAsc = !sortAsc;
      } else {
        currentSort = sortKey;
        sortAsc = true;
      }
      performSort(sortKey, sortAsc);
      updateSortIndicators(el, sortAsc);
      saveState();
    });
  });

  function performSort(key, asc) {
    const pairs = getBookPairs();
    pairs.sort(function (a, b) {
      let valA = a.row.dataset[key] || '';
      let valB = b.row.dataset[key] || '';

      // Numeric sort for rating, prices
      if (key === 'rating' || key === 'purchasePrice' || key === 'sellPrice') {
        valA = parseFloat(valA) || 0;
        valB = parseFloat(valB) || 0;
      }

      if (valA < valB) return asc ? -1 : 1;
      if (valA > valB) return asc ? 1 : -1;
      return 0;
    });

    // Reorder DOM: insert after header
    let insertAfter = header;
    pairs.forEach(function (pair) {
      insertAfter.after(pair.row);
      insertAfter = pair.row;
      if (pair.detail) {
        insertAfter.after(pair.detail);
        insertAfter = pair.detail;
      }
    });
    // Move empty message to end
    if (emptyMessage) container.appendChild(emptyMessage);
  }

  function updateSortIndicators(activeEl, asc) {
    sortables.forEach(function (el) {
      const indicator = el.querySelector('.books__sort-indicator');
      if (el === activeEl) {
        indicator.textContent = asc ? ' \u25B2' : ' \u25BC';
      } else {
        indicator.textContent = '';
      }
    });
  }

  // --- Filtering ---
  let activeFilter = null;
  const filterButtons = document.querySelectorAll('.book-filter');

  filterButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const filter = btn.dataset.filter;
      if (activeFilter === filter || filter === 'all') {
        activeFilter = null;
        applyFilter(null);
      } else {
        activeFilter = filter;
        applyFilter(filter);
      }
      updateFilterButtons();
      saveState();
    });
  });

  function applyFilter(filter) {
    const pairs = getBookPairs();
    let visibleCount = 0;
    pairs.forEach(function (pair) {
      const status = pair.row.dataset.status;
      const show = !filter || status === filter;
      pair.row.classList.toggle('books__hidden', !show);
      if (pair.detail) {
        if (!show) {
          pair.detail.classList.remove('books__detail--open');
          pair.detail.classList.add('books__hidden');
          // Reset chevron
          const chevron = pair.row.querySelector('.books__chevron');
          if (chevron) chevron.classList.remove('books__chevron--open');
        } else {
          pair.detail.classList.remove('books__hidden');
        }
      }
      if (show) visibleCount++;
    });
    if (emptyMessage) {
      emptyMessage.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  }

  function updateFilterButtons() {
    filterButtons.forEach(function (btn) {
      const isActive = activeFilter && btn.dataset.filter === activeFilter;
      btn.classList.toggle('book-filter--active', isActive);
    });
  }

  // --- Detail toggle ---
  container.addEventListener('click', function (e) {
    const chevron = e.target.closest('.books__chevron');
    if (!chevron) return;
    e.preventDefault();
    const detailId = chevron.dataset.detail;
    const detail = document.getElementById(detailId);
    if (!detail) return;
    chevron.classList.toggle('books__chevron--open');
    detail.classList.toggle('books__detail--open');
  });

  // --- URL hash state persistence ---
  function saveState() {
    const parts = [];
    if (currentSort) {
      parts.push('sort=' + currentSort);
      parts.push('dir=' + (sortAsc ? 'asc' : 'desc'));
    }
    if (activeFilter) {
      parts.push('filter=' + activeFilter);
    }
    window.location.hash = parts.length ? parts.join('&') : '';
  }

  function restoreState() {
    const hash = window.location.hash.replace('#', '');
    if (!hash) return;
    const params = {};
    hash.split('&').forEach(function (part) {
      const kv = part.split('=');
      if (kv.length === 2) params[kv[0]] = kv[1];
    });

    if (params.sort) {
      currentSort = params.sort;
      sortAsc = params.dir !== 'desc';
      performSort(currentSort, sortAsc);
      // Find matching sortable and update indicator
      sortables.forEach(function (el) {
        if (el.dataset.sort === currentSort) {
          updateSortIndicators(el, sortAsc);
        }
      });
    }

    if (params.filter && params.filter !== 'all') {
      activeFilter = params.filter;
      applyFilter(activeFilter);
      updateFilterButtons();
    }
  }

  restoreState();
});
