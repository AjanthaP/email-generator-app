// Popup UI Logic
document.addEventListener('DOMContentLoaded', async () => {
  // Load saved settings
  await loadSettings();
  
  // Check API health
  await checkApiHealth();
  
  // Load usage stats
  await loadUsageStats();
  
  // Set up event listeners
  setupEventListeners();
});

// Load settings from storage
async function loadSettings() {
  try {
    const result = await chrome.storage.sync.get(['apiKey', 'tone']);
    
    if (result.apiKey) {
      document.getElementById('apiKey').value = result.apiKey;
    }
    
    if (result.tone) {
      document.getElementById('toneSelect').value = result.tone;
    }
  } catch (error) {
    console.error('Failed to load settings:', error);
  }
}

// Save settings to storage
async function saveSettings() {
  const apiKey = document.getElementById('apiKey').value.trim();
  const tone = document.getElementById('toneSelect').value;
  const statusEl = document.getElementById('saveStatus');
  
  if (!apiKey) {
    showStatus(statusEl, 'Please enter an API key', 'error');
    return;
  }
  
  try {
    await chrome.storage.sync.set({ apiKey, tone });
    showStatus(statusEl, '✓ Settings saved successfully!', 'success');
    
    // Recheck API health with new key
    await checkApiHealth();
  } catch (error) {
    console.error('Failed to save settings:', error);
    showStatus(statusEl, '✗ Failed to save settings', 'error');
  }
}

// Check API health
async function checkApiHealth() {
  const statusDot = document.querySelector('.status-dot');
  const statusText = document.getElementById('statusText');
  
  try {
    const response = await chrome.runtime.sendMessage({
      action: 'healthCheck'
    });
    
    if (response.success) {
      statusDot.className = 'status-dot online';
      statusText.textContent = 'Connected';
    } else {
      statusDot.className = 'status-dot offline';
      statusText.textContent = 'Disconnected';
    }
  } catch (error) {
    console.error('Health check failed:', error);
    statusDot.className = 'status-dot offline';
    statusText.textContent = 'Error';
  }
}

// Load usage statistics
async function loadUsageStats() {
  const draftsEl = document.getElementById('draftsToday');
  const quotaEl = document.getElementById('quotaRemaining');
  
  try {
    const response = await chrome.runtime.sendMessage({
      action: 'checkUsage'
    });
    
    if (response.success) {
      draftsEl.textContent = response.data.drafts_today || 0;
      quotaEl.textContent = response.data.quota_remaining === null 
        ? 'Unlimited' 
        : response.data.quota_remaining;
    } else {
      draftsEl.textContent = '-';
      quotaEl.textContent = '-';
    }
  } catch (error) {
    console.error('Failed to load usage stats:', error);
    draftsEl.textContent = 'Error';
    quotaEl.textContent = 'Error';
  }
}

// Quick generate draft
async function generateQuickDraft() {
  const recipient = document.getElementById('quickRecipient').value.trim();
  const subject = document.getElementById('quickSubject').value.trim();
  const context = document.getElementById('quickContext').value.trim();
  const resultEl = document.getElementById('quickResult');
  const generateBtn = document.getElementById('generateQuick');
  
  if (!context) {
    showResult(resultEl, 'Please provide context for the email', null, 'error');
    return;
  }
  
  // Disable button and show loading
  generateBtn.disabled = true;
  generateBtn.textContent = 'Generating...';
  resultEl.className = 'quick-result';
  resultEl.style.display = 'none';
  
  try {
    const tone = document.getElementById('toneSelect').value;
    
    const response = await chrome.runtime.sendMessage({
      action: 'generateDraft',
      data: {
        recipient: recipient || null,
        subject: subject || null,
        context: context,
        tone: tone
      }
    });
    
    if (response.success) {
      showResult(resultEl, 'Draft generated successfully!', response.data.draft, 'success');
      
      // Refresh usage stats
      await loadUsageStats();
    } else {
      showResult(resultEl, response.error || 'Failed to generate draft', null, 'error');
    }
  } catch (error) {
    console.error('Generate failed:', error);
    showResult(resultEl, 'An error occurred while generating the draft', null, 'error');
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = 'Generate Draft';
  }
}

// Show status message
function showStatus(element, message, type) {
  element.textContent = message;
  element.className = `save-status ${type}`;
  
  setTimeout(() => {
    element.style.display = 'none';
  }, 3000);
}

// Show result with draft text
function showResult(element, message, draftText, type) {
  element.className = `quick-result ${type}`;
  
  if (draftText) {
    element.innerHTML = `
      <strong>${message}</strong>
      <pre>${escapeHtml(draftText)}</pre>
      <button onclick="copyToClipboard('${escapeHtml(draftText).replace(/'/g, "\\'")}')">Copy to Clipboard</button>
    `;
  } else {
    element.textContent = message;
  }
  
  element.style.display = 'block';
}

// Copy text to clipboard
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    const resultEl = document.getElementById('quickResult');
    const originalHtml = resultEl.innerHTML;
    resultEl.innerHTML = '<strong>✓ Copied to clipboard!</strong>';
    
    setTimeout(() => {
      resultEl.innerHTML = originalHtml;
    }, 2000);
  }).catch(err => {
    console.error('Failed to copy:', err);
  });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Toggle API key visibility
function toggleApiKeyVisibility() {
  const input = document.getElementById('apiKey');
  const button = document.getElementById('toggleApiKey');
  
  if (input.type === 'password') {
    input.type = 'text';
    button.textContent = '🙈';
  } else {
    input.type = 'password';
    button.textContent = '👁️';
  }
}

// Set up all event listeners
function setupEventListeners() {
  document.getElementById('saveSettings').addEventListener('click', saveSettings);
  document.getElementById('generateQuick').addEventListener('click', generateQuickDraft);
  document.getElementById('refreshUsage').addEventListener('click', loadUsageStats);
  document.getElementById('toggleApiKey').addEventListener('click', toggleApiKeyVisibility);
  
  // Enter key in quick context textarea
  document.getElementById('quickContext').addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      generateQuickDraft();
    }
  });
}
