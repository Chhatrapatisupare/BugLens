/**
 * BugLens UI Utility Module
 * Manages toasts, modals, badges, exports, and DOM formatting.
 */
const UI = {
  /**
   * Display a clean toast message
   */
  toast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(8px)';
      toast.style.transition = 'all 0.2s ease';
      setTimeout(() => toast.remove(), 250);
    }, duration);
  },

  /**
   * Return HTML string for severity badge
   */
  renderSeverityBadge(severity) {
    const s = (severity || 'Medium').toLowerCase();
    return `<span class="badge badge-${s}">${severity || 'Medium'}</span>`;
  },

  /**
   * Return HTML string for priority badge
   */
  renderPriorityBadge(priority) {
    const p = (priority || 'P2').toLowerCase();
    return `<span class="badge badge-${p}">${priority || 'P2'}</span>`;
  },

  /**
   * Return HTML string for category badge
   */
  renderCategoryBadge(category) {
    return `<span class="badge badge-category">${category || 'Unclassified'}</span>`;
  },

  /**
   * Format ISO date string to human-readable date
   */
  formatDate(dateStr) {
    if (!dateStr) return 'Just now';
    try {
      const d = new Date(dateStr);
      return isNaN(d.getTime()) ? dateStr : d.toLocaleString();
    } catch {
      return dateStr;
    }
  },

  /**
   * Confirm action using accessible modal dialog
   */
  confirm(title, message, onConfirm) {
    const modal = document.getElementById('app-modal');
    if (!modal) {
      if (window.confirm(message)) onConfirm();
      return;
    }

    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').textContent = message;

    const confirmBtn = document.getElementById('modal-confirm-btn');
    const cancelBtn = document.getElementById('modal-cancel-btn');

    const handleConfirm = () => {
      modal.classList.remove('active');
      confirmBtn.removeEventListener('click', handleConfirm);
      onConfirm();
    };

    const handleCancel = () => {
      modal.classList.remove('active');
      confirmBtn.removeEventListener('click', handleConfirm);
    };

    confirmBtn.onclick = handleConfirm;
    cancelBtn.onclick = handleCancel;
    modal.classList.add('active');
  },

  /**
   * Export JSON data as downloadable file
   */
  downloadJSON(data, filename = 'buglens-analysis.json') {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    UI.toast('Analysis exported as JSON file.', 'success');
  },

  /**
   * Print report using browser print styling
   */
  printReport() {
    window.print();
  }
};

window.UI = UI;
