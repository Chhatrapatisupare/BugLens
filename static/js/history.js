/**
 * BugLens History Controller
 * Handles search, category/severity filtering, report navigation,
 * and deletion with confirmation modal.
 */
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('history-search');
  const categoryFilter = document.getElementById('filter-category');
  const severityFilter = document.getElementById('filter-severity');
  const tableBody = document.getElementById('history-table-body');
  const emptyState = document.getElementById('history-empty-state');
  const countBadge = document.getElementById('history-count-badge');

  let debounceTimer = null;

  async function loadHistory() {
    const filters = {
      search: searchInput ? searchInput.value.trim() : '',
      category: categoryFilter ? categoryFilter.value : '',
      severity: severityFilter ? severityFilter.value : ''
    };

    try {
      const res = await API.getHistory(filters);
      const reports = res.reports || [];

      if (countBadge) {
        countBadge.textContent = `${reports.length} report${reports.length === 1 ? '' : 's'}`;
      }

      if (reports.length === 0) {
        if (tableBody) tableBody.innerHTML = '';
        if (emptyState) emptyState.style.display = 'block';
        return;
      }

      if (emptyState) emptyState.style.display = 'none';
      if (tableBody) {
        tableBody.innerHTML = reports.map(r => `
          <tr id="history-row-${r.id}">
            <td><strong>#${r.id}</strong></td>
            <td>
              <a href="/result/${r.id}" style="font-weight: 600; color: var(--text-primary);">
                ${escapeHtml(r.title)}
              </a>
              <div style="font-size: 0.78rem; color: var(--text-muted);">${escapeHtml(r.summary || r.component || '')}</div>
            </td>
            <td>${UI.renderCategoryBadge(r.category)}</td>
            <td>${UI.renderSeverityBadge(r.severity)}</td>
            <td>${UI.renderPriorityBadge(r.priority)}</td>
            <td>${Math.round((r.confidence || 0.85) * 100)}%</td>
            <td style="font-size: 0.8rem; color: var(--text-muted);">${UI.formatDate(r.created_at)}</td>
            <td>
              <div style="display: flex; gap: 0.35rem;">
                <a href="/result/${r.id}" class="btn btn-secondary btn-sm" title="View Full Report">View</a>
                <button class="btn btn-danger btn-sm" onclick="handleDeleteReport(${r.id})" title="Delete Record">Delete</button>
              </div>
            </td>
          </tr>
        `).join('');
      }
    } catch (err) {
      console.error('Error fetching history:', err);
      UI.toast('Failed to load history: ' + err.message, 'error');
    }
  }

  // Bind live filters
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(loadHistory, 300);
    });
  }

  if (categoryFilter) {
    categoryFilter.addEventListener('change', loadHistory);
  }

  if (severityFilter) {
    severityFilter.addEventListener('change', loadHistory);
  }

  // Initial load
  loadHistory();

  // Expose delete handler globally
  window.handleDeleteReport = (reportId) => {
    UI.confirm(
      'Delete Analysis Report',
      `Are you sure you want to delete report #${reportId}? This action cannot be undone.`,
      async () => {
        try {
          await API.deleteReport(reportId);
          UI.toast(`Report #${reportId} deleted successfully.`, 'success');
          const row = document.getElementById(`history-row-${reportId}`);
          if (row) row.remove();
          loadHistory(); // refresh count
        } catch (err) {
          UI.toast(err.message, 'error');
        }
      }
    );
  };
});

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
