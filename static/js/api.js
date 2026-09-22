/**
 * BugLens API Client Module
 * Provides unified HTTP fetch routines for Flask endpoints with structured error handling.
 */
const API = {
  /**
   * Health check and configuration status
   */
  async getHealth() {
    const res = await fetch('/api/health');
    return await res.json();
  },

  /**
   * Dashboard statistics and recent analyses
   */
  async getDashboard() {
    const res = await fetch('/api/dashboard');
    if (!res.ok) throw new Error('Failed to load dashboard metrics');
    return await res.json();
  },

  /**
   * Retrieve preset sample bugs
   */
  async getSampleBugs() {
    const res = await fetch('/api/sample-bugs');
    if (!res.ok) throw new Error('Failed to fetch sample bugs');
    return await res.json();
  },

  /**
   * Submit bug report to Agentic AI pipeline
   */
  async analyzeBug(payload) {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Bug analysis failed');
    }
    return data.data;
  },

  /**
   * Retrieve history records with optional filters
   */
  async getHistory(filters = {}) {
    const params = new URLSearchParams();
    if (filters.search) params.append('search', filters.search);
    if (filters.category) params.append('category', filters.category);
    if (filters.severity) params.append('severity', filters.severity);

    const url = `/api/history?${params.toString()}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch analysis history');
    return await res.json();
  },

  /**
   * Retrieve single analysis report by ID
   */
  async getReport(reportId) {
    const res = await fetch(`/api/history/${reportId}`);
    if (!res.ok) throw new Error(`Report #${reportId} not found`);
    return await res.json();
  },

  /**
   * Delete report by ID
   */
  async deleteReport(reportId) {
    const res = await fetch(`/api/history/${reportId}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Failed to delete report');
    }
    return data;
  }
};

window.API = API;
