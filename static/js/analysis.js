/**
 * BugLens New Analysis Controller
 * Manages form state, sample report loading, multi-agent pipeline progress tracker,
 * and result handoff.
 */
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('bug-report-form');
  const analyzeBtn = document.getElementById('analyze-btn');
  const sampleSelect = document.getElementById('sample-bug-select');
  const loadSampleBtn = document.getElementById('load-sample-btn');
  const trackerCard = document.getElementById('pipeline-tracker-card');

  let sampleDataCache = [];

  // 1. Fetch available sample bugs for the dropdown
  async function initSampleBugs() {
    try {
      const res = await API.getSampleBugs();
      if (res.success && res.samples && res.samples.length > 0) {
        sampleDataCache = res.samples;
        if (sampleSelect) {
          sampleSelect.innerHTML = '<option value="">-- Select a Pre-configured Example --</option>' +
            res.samples.map(s => `<option value="${s.id}">${escapeHtml(s.title)}</option>`).join('');
        }
      }
    } catch (e) {
      console.warn('Could not preload sample bugs:', e);
    }
  }

  initSampleBugs();

  // 2. Handle "Load Example" Click
  if (loadSampleBtn) {
    loadSampleBtn.addEventListener('click', () => {
      const selectedId = sampleSelect ? sampleSelect.value : '';
      let targetSample = sampleDataCache.find(s => s.id === selectedId);
      if (!targetSample && sampleDataCache.length > 0) {
        targetSample = sampleDataCache[0]; // fallback to first sample
      }

      if (targetSample) {
        document.getElementById('bug-title').value = targetSample.title || '';
        document.getElementById('bug-description').value = targetSample.description || '';
        document.getElementById('bug-expected').value = targetSample.expected_behavior || '';
        document.getElementById('bug-actual').value = targetSample.actual_behavior || '';
        document.getElementById('bug-steps').value = targetSample.steps_to_reproduce || '';
        document.getElementById('bug-environment').value = targetSample.environment || '';
        document.getElementById('bug-error-log').value = targetSample.error_log || '';
        document.getElementById('bug-stack-trace').value = targetSample.stack_trace || '';
        document.getElementById('bug-component').value = targetSample.component || '';
        document.getElementById('bug-labels').value = targetSample.existing_labels || '';

        UI.toast('Example bug loaded. You can edit any field before analyzing.', 'info');
      } else {
        UI.toast('No example selected.', 'warning');
      }
    });
  }

  // 3. Handle Form Submission
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const payload = {
        title: document.getElementById('bug-title').value.trim(),
        description: document.getElementById('bug-description').value.trim(),
        expected_behavior: document.getElementById('bug-expected').value.trim(),
        actual_behavior: document.getElementById('bug-actual').value.trim(),
        steps_to_reproduce: document.getElementById('bug-steps').value.trim(),
        environment: document.getElementById('bug-environment').value.trim(),
        error_log: document.getElementById('bug-error-log').value.trim(),
        stack_trace: document.getElementById('bug-stack-trace').value.trim(),
        component: document.getElementById('bug-component').value.trim(),
        existing_labels: document.getElementById('bug-labels').value.trim()
      };

      // Simple client-side validation
      if (!payload.title || payload.title.length < 5) {
        UI.toast('Please provide a descriptive Bug Title (at least 5 chars).', 'warning');
        document.getElementById('bug-title').focus();
        return;
      }
      if (!payload.description) {
        UI.toast('Bug Description is required.', 'warning');
        document.getElementById('bug-description').focus();
        return;
      }
      if (!payload.expected_behavior || !payload.actual_behavior) {
        UI.toast('Both Expected and Actual behaviors are required.', 'warning');
        return;
      }
      if (!payload.steps_to_reproduce) {
        UI.toast('Steps to Reproduce are required.', 'warning');
        document.getElementById('bug-steps').focus();
        return;
      }
      if (!payload.environment) {
        UI.toast('Environment specification is required (OS, language, runtime, etc.).', 'warning');
        document.getElementById('bug-environment').focus();
        return;
      }

      // Lock UI & Show Stepper
      analyzeBtn.disabled = true;
      analyzeBtn.innerHTML = '<span class="status-dot demo" style="margin-right:6px;"></span> Analyzing with Agentic Pipeline...';
      if (trackerCard) trackerCard.style.display = 'block';

      // Start stepping animation
      const stopProgress = runPipelineStepper();

      try {
        const result = await API.analyzeBug(payload);
        stopProgress(true);

        UI.toast('Analysis complete! Redirecting to report...', 'success');
        setTimeout(() => {
          window.location.href = `/result/${result.id}`;
        }, 800);
      } catch (err) {
        stopProgress(false);
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '⚡ Analyze Bug with Agents';
        UI.toast('Analysis failed: ' + err.message, 'error');
      }
    });
  }
});

/**
 * Animates the 7 stages of the agent pipeline during request execution
 */
function runPipelineStepper() {
  const steps = [
    { id: 'step-validation', name: 'Input Validation', desc: 'Validating payload syntax & required fields' },
    { id: 'step-understanding', name: 'Bug Understanding Agent', desc: 'Extracting symptoms & technical entities' },
    { id: 'step-classification', name: 'Classification Agent', desc: 'Determining category, severity & priority' },
    { id: 'step-research', name: 'Tavily Research Agent', desc: 'Retrieving technical documentation & sources' },
    { id: 'step-evidence', name: 'Evidence Analysis Agent', desc: 'Corroborating symptoms with technical facts' },
    { id: 'step-recommendations', name: 'Recommendation Agent', desc: 'Generating debugging & testing procedures' },
    { id: 'step-report', name: 'Final Report Generator', desc: 'Synthesizing report & saving triage record' }
  ];

  let currentIdx = 0;

  // Reset steps in UI
  steps.forEach(s => {
    const el = document.getElementById(s.id);
    if (el) {
      el.className = 'pipeline-step';
      const ind = el.querySelector('.step-indicator');
      if (ind) ind.textContent = '○';
    }
  });

  function updateStep(index) {
    if (index >= steps.length) return;
    const current = document.getElementById(steps[index].id);
    if (current) {
      current.className = 'pipeline-step running';
      const ind = current.querySelector('.step-indicator');
      if (ind) ind.textContent = '●';
    }
    // Mark previous as completed
    if (index > 0) {
      const prev = document.getElementById(steps[index - 1].id);
      if (prev) {
        prev.className = 'pipeline-step completed';
        const ind = prev.querySelector('.step-indicator');
        if (ind) ind.textContent = '✓';
      }
    }
  }

  updateStep(0);
  const interval = setInterval(() => {
    currentIdx++;
    if (currentIdx < steps.length) {
      updateStep(currentIdx);
    }
  }, 900);

  return function finish(success) {
    clearInterval(interval);
    if (success) {
      steps.forEach(s => {
        const el = document.getElementById(s.id);
        if (el) {
          el.className = 'pipeline-step completed';
          const ind = el.querySelector('.step-indicator');
          if (ind) ind.textContent = '✓';
        }
      });
    }
  };
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
