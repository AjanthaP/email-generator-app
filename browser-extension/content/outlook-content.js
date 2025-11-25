/**
 * Outlook Content Script - Inject AI Draft button into Outlook compose
 */

console.log('[AI Draft] Outlook content script loaded');

// Wait for Outlook to load
function waitForOutlook() {
  return new Promise((resolve) => {
    const checkInterval = setInterval(() => {
      const composeBox = document.querySelector('[role="region"][aria-label*="compose"]') ||
                         document.querySelector('[aria-label*="Message body"]');
      if (composeBox) {
        clearInterval(checkInterval);
        resolve();
      }
    }, 500);
    
    setTimeout(() => {
      clearInterval(checkInterval);
      resolve();
    }, 10000);
  });
}

// Inject AI button into Outlook compose
function injectOutlookButton() {
  const composeAreas = document.querySelectorAll('[role="region"][aria-label*="compose"]');
  
  composeAreas.forEach((composeArea) => {
    if (composeArea.querySelector('.ai-draft-button')) return;
    
    // Find toolbar
    let toolbar = composeArea.querySelector('[role="toolbar"]');
    if (!toolbar) {
      toolbar = composeArea.querySelector('.ms-CommandBar');
    }
    
    if (!toolbar) {
      console.log('[AI Draft] Toolbar not found in Outlook compose');
      return;
    }
    
    // Create AI button
    const aiButton = document.createElement('div');
    aiButton.className = 'ai-draft-button outlook-style';
    aiButton.innerHTML = `
      <button class="ai-generate-btn" title="Generate AI Draft">
        ✨ AI Draft
      </button>
    `;
    
    toolbar.appendChild(aiButton);
    
    aiButton.querySelector('.ai-generate-btn').addEventListener('click', () => {
      handleOutlookGenerate(composeArea);
    });
    
    console.log('[AI Draft] Button injected into Outlook compose');
  });
}

// Handle generate for Outlook
async function handleOutlookGenerate(composeArea) {
  try {
    const toField = composeArea.querySelector('[aria-label*="To"]') ||
                    document.querySelector('[aria-label*="To"]');
    const recipient = toField ? toField.textContent.trim() : '';
    
    const subjectField = document.querySelector('[aria-label*="Subject"]');
    const subject = subjectField ? (subjectField.value || subjectField.textContent).trim() : '';
    
    const bodyField = composeArea.querySelector('[role="textbox"]') ||
                      document.querySelector('[aria-label*="Message body"]');
    const existingText = bodyField ? bodyField.textContent.trim() : '';
    
    if (!recipient && !subject && !existingText) {
      showError(composeArea, 'Please provide at least a recipient, subject, or some context.');
      return;
    }
    
    showLoading(composeArea);
    
    const tone = await getSavedTone();
    
    const response = await chrome.runtime.sendMessage({
      action: 'generateDraft',
      data: {
        recipient,
        subject,
        context: existingText,
        tone
      }
    });
    
    hideLoading(composeArea);
    
    if (response.error) {
      showError(composeArea, response.error);
      return;
    }
    
    if (bodyField && response.draft) {
      bodyField.focus();
      bodyField.textContent = response.draft;
      bodyField.dispatchEvent(new Event('input', { bubbles: true }));
      
      console.log('[AI Draft] Draft inserted into Outlook');
      showSuccess(composeArea, `Draft generated! (${response.word_count} words)`);
    }
    
  } catch (error) {
    console.error('[AI Draft] Error:', error);
    hideLoading(composeArea);
    showError(composeArea, 'Failed to generate draft. Please try again.');
  }
}

// Reuse helper functions (same as Gmail)
async function getSavedTone() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['tone'], (result) => {
      resolve(result.tone || 'professional');
    });
  });
}

function showLoading(container) {
  hideLoading(container);
  const loader = document.createElement('div');
  loader.className = 'ai-draft-loader';
  loader.innerHTML = `
    <div class="spinner"></div>
    <span>Generating draft...</span>
  `;
  container.appendChild(loader);
}

function hideLoading(container) {
  const loader = container.querySelector('.ai-draft-loader');
  if (loader) loader.remove();
}

function showError(container, message) {
  const errorBox = document.createElement('div');
  errorBox.className = 'ai-draft-error';
  errorBox.textContent = `❌ ${message}`;
  container.appendChild(errorBox);
  setTimeout(() => errorBox.remove(), 5000);
}

function showSuccess(container, message) {
  const successBox = document.createElement('div');
  successBox.className = 'ai-draft-success';
  successBox.textContent = `✅ ${message}`;
  container.appendChild(successBox);
  setTimeout(() => successBox.remove(), 3000);
}

// Initialize
waitForOutlook().then(() => {
  console.log('[AI Draft] Outlook detected, injecting button');
  injectOutlookButton();
  
  const observer = new MutationObserver(() => {
    injectOutlookButton();
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
});
