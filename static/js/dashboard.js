/**
 * BugLens Dashboard Controller
 * Fetches and displays real-time aggregated metrics and recent analyses.
 */
document.addEventListener('DOMContentLoaded', async () => {
  const totalCountEl = document.getElementById('metric-total');
  const criticalCountEl = document.getElementById('metric-critical');
  const highPriorityEl = document.getElementById('metric-high-priority');
  const commonCategoryEl = document.getElementById('metric-common-category');
  const recentTableBody = document.getElementById('recent-table-body');
  const zeroStateEl = document.getElementById('zero-state-container');
  const recentCardEl = document.getElementById('recent-analyses-card');
  const categoryPillsContainer = document.getElementById('category-pills-container');

  try {
    const res = await API.getDashboard();
    const metrics = res.metrics;

    if (!metrics || metrics.total === 0) {
      if (totalCountEl) totalCountEl.textContent = '0';
      if (criticalCountEl) criticalCountEl.textContent = '0';
      if (highPriorityEl) highPriorityEl.textContent = '0';
      if (commonCategoryEl) commonCategoryEl.textContent = 'None';
      if (zeroStateEl) zeroStateEl.style.display = 'block';
      if (recentCardEl) recentCardEl.style.display = 'none';
      return;
    }

    // Populate KPI cards
    if (totalCountEl) totalCountEl.textContent = metrics.total;
    if (criticalCountEl) criticalCountEl.textContent = metrics.critical_count;
    if (highPriorityEl) highPriorityEl.textContent = metrics.high_priority_count;
    if (commonCategoryEl) commonCategoryEl.textContent = metrics.most_common_category;

    // Render Category Distribution Pills
    if (categoryPillsContainer && metrics.category_breakdown) {
      categoryPillsContainer.innerHTML = '';
      for (const [cat, count] of Object.entries(metrics.category_breakdown)) {
        const pill = document.createElement('span');
        pill.className = 'tag';
        pill.innerHTML = `<strong>${cat}</strong>: ${count}`;
        categoryPillsContainer.appendChild(pill);
      }
    }

    // Populate Recent Analyses Table
    if (recentTableBody && metrics.recent_reports && metrics.recent_reports.length > 0) {
      if (zeroStateEl) zeroStateEl.style.display = 'none';
      if (recentCardEl) recentCardEl.style.display = 'block';

      recentTableBody.innerHTML = metrics.recent_reports.map(report => `
        <tr>
          <td><strong>#${report.id}</strong></td>
          <td>
            <a href="/result/${report.id}" style="font-weight: 600;">
              ${escapeHtml(report.title)}
            </a>
            <div style="font-size: 0.78rem; color: var(--text-muted);">${escapeHtml(report.component || 'General')}</div>
          </td>
          <td>${UI.renderCategoryBadge(report.category)}</td>
          <td>${UI.renderSeverityBadge(report.severity)}</td>
          <td>${UI.renderPriorityBadge(report.priority)}</td>
          <td>${Math.round((report.confidence || 0.85) * 100)}%</td>
          <td style="font-size: 0.8rem; color: var(--text-muted);">${UI.formatDate(report.created_at)}</td>
          <td>
            <a href="/result/${report.id}" class="btn btn-secondary btn-sm">Inspect</a>
          </td>
        </tr>
      `).join('');
    }
  } catch (error) {
    console.error('Error loading dashboard:', error);
    UI.toast('Failed to load dashboard metrics: ' + error.message, 'error');
  }
});

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
