/**
 * Gmail Content Script - Inject AI Draft button into Gmail compose
 */

console.log('[AI Draft] Gmail content script loaded');
// Diagnostics for chrome storage availability
try {
  const hasChrome = typeof chrome !== 'undefined';
  const hasStorage = hasChrome && !!(chrome && chrome.storage);
  const hasSync = hasStorage && !!(chrome.storage && chrome.storage.sync);
  console.log('[AI Draft][Diagnostics] chrome:', hasChrome, 'storage:', hasStorage, 'sync:', hasSync);
} catch (e) {
  console.warn('[AI Draft][Diagnostics] Error checking chrome.storage', e);
}

// Wait for Gmail to load
function waitForGmail() {
  return new Promise((resolve) => {
    console.log('[AI Draft] Waiting for Gmail compose box...');
    const checkInterval = setInterval(() => {
      const composeBox = document.querySelector('[role="dialog"]');
      if (composeBox) {
        console.log('[AI Draft] Compose box found!');
        clearInterval(checkInterval);
        resolve();
      }
    }, 500);
    
    // Timeout after 10 seconds
    setTimeout(() => {
      console.log('[AI Draft] Timeout - checking anyway');
      clearInterval(checkInterval);
      resolve();
    }, 10000);
  });
}

// Inject AI button into Gmail compose
function injectGmailButton() {
  console.log('[AI Draft] Attempting to inject button...');
  const composeBoxes = document.querySelectorAll('[role="dialog"]');
  console.log(`[AI Draft] Found ${composeBoxes.length} compose boxes`);
  
  composeBoxes.forEach((composeBox, index) => {
    // Check if button already exists
    if (composeBox.querySelector('.ai-draft-button')) {
      console.log(`[AI Draft] Button already exists in compose box ${index}`);
      return;
    }
    
    // Find the toolbar - try multiple selectors
    let toolbar = composeBox.querySelector('[role="toolbar"]');
    
    if (!toolbar) {
      // Try alternative selectors - look for the formatting toolbar
      toolbar = composeBox.querySelector('table[role="group"]');
    }
    
    if (!toolbar) {
      // Try finding the send button's parent
      const sendButton = composeBox.querySelector('[aria-label*="Send"]');
      if (sendButton) {
        toolbar = sendButton.closest('tr') || sendButton.closest('td') || sendButton.parentElement;
      }
    }
    
    if (!toolbar) {
      console.warn(`[AI Draft] Toolbar not found in compose box ${index}`);
      console.log('[AI Draft] Compose box structure:', composeBox.outerHTML.substring(0, 500));
      
      // Last resort: inject at the top of the compose box
      toolbar = composeBox.querySelector('[role="heading"]')?.parentElement;
      if (toolbar) {
        console.log('[AI Draft] Using compose header as fallback');
      } else {
        return;
      }
    }
    
    console.log(`[AI Draft] Toolbar found in compose box ${index}`);
    
    // Create AI controls container
    const aiButton = document.createElement('div');
    aiButton.className = 'ai-draft-button';
    aiButton.style.cssText = 'display:inline-flex;align-items:center;gap:6px;margin-left:8px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;';
    aiButton.innerHTML = `
      <select class="ai-tone-select" title="Tone" style="padding:4px 6px;border:1px solid #ccc;border-radius:4px;font-size:12px;background:#fff;">
        <option value="professional">Professional</option>
        <option value="friendly">Friendly</option>
        <option value="formal">Formal</option>
        <option value="casual">Casual</option>
        <option value="enthusiastic">Enthusiastic</option>
      </select>
      <select class="ai-length-select" title="Length" style="padding:4px 6px;border:1px solid #ccc;border-radius:4px;font-size:12px;background:#fff;">
        <option value="auto">Length: Auto</option>
        <option value="short">Short</option>
        <option value="medium" selected>Medium</option>
        <option value="long">Long</option>
      </select>
      <button class="ai-generate-btn" title="Generate AI Draft" style="
        background: linear-gradient(135deg,#667eea 0%,#764ba2 100%);
        color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:500;letter-spacing:.3px;">
        ✨ AI Draft
      </button>
    `;
    
    // Preferred insertion: next to (before) send button for clear separation
    const sendButton = composeBox.querySelector('[aria-label*="Send"]');
    if (sendButton) {
      const sendParent = sendButton.closest('div,td,tr');
      if (sendParent) {
        // Insert before the send button's container (to the left of Send)
        sendParent.parentElement?.insertBefore(aiButton, sendParent);
      } else {
        // Fallback: insert directly before send button
        sendButton.parentElement?.insertBefore(aiButton, sendButton);
      }
    } else {
      // No send button found, insert at start of toolbar
      toolbar.insertBefore(aiButton, toolbar.firstChild);
    }
    console.log(`[AI Draft] Button injected into compose box ${index}`);
    console.log(`[AI Draft] Button element:`, aiButton);
    console.log(`[AI Draft] Button visible:`, aiButton.offsetWidth > 0 && aiButton.offsetHeight > 0);
    
    // Add click handler
    aiButton.querySelector('.ai-generate-btn').addEventListener('click', () => {
      const toneSelect = aiButton.querySelector('.ai-tone-select');
      const lengthSelect = aiButton.querySelector('.ai-length-select');
      const tone = toneSelect ? toneSelect.value : 'professional';
      const lengthPref = lengthSelect ? lengthSelect.value : 'auto';
      // Persist selections with safe fallback
      savePrefs({ tone, length_preference: lengthPref });
      handleGmailGenerate(composeBox, tone, lengthPref);
    });

    // Load saved preferences (safe)
    loadPrefs().then(res => {
      if (res.tone) {
        const toneSelect = aiButton.querySelector('.ai-tone-select');
        if (toneSelect) toneSelect.value = res.tone;
      }
      if (res.length_preference) {
        const lengthSelect = aiButton.querySelector('.ai-length-select');
        if (lengthSelect) lengthSelect.value = res.length_preference;
      }
    });

    // Fallback floating panel if hidden (minimized compose)
    if (!(aiButton.offsetWidth > 0 && aiButton.offsetHeight > 0)) {
      console.log('[AI Draft] Creating floating fallback panel');
      const panel = document.createElement('div');
      panel.style.cssText = 'position:absolute;bottom:52px;right:12px;display:flex;flex-direction:row;gap:6px;background:#ffffffEE;border:1px solid #ddd;padding:6px 8px;border-radius:8px;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,.15);backdrop-filter:blur(4px);';
      panel.innerHTML = `
        <select class="ai-tone-select" style="padding:2px 4px;font-size:11px;border:1px solid #ccc;border-radius:4px;">
          <option value="professional">Pro</option>
          <option value="friendly">Friendly</option>
          <option value="formal">Formal</option>
          <option value="casual">Casual</option>
          <option value="enthusiastic">Excited</option>
        </select>
        <select class="ai-length-select" style="padding:2px 4px;font-size:11px;border:1px solid #ccc;border-radius:4px;">
          <option value="auto">Auto</option>
          <option value="short">Short</option>
          <option value="medium" selected>Med</option>
          <option value="long">Long</option>
        </select>
        <button class="ai-floating-generate" style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;padding:4px 10px;border-radius:6px;font-size:12px;cursor:pointer;">✨ Draft</button>
      `;
      composeBox.style.position = 'relative';
      composeBox.appendChild(panel);
      const floatBtn = panel.querySelector('.ai-floating-generate');
      floatBtn.addEventListener('click', () => {
        const toneSelect = panel.querySelector('.ai-tone-select');
        const lengthSelect = panel.querySelector('.ai-length-select');
        const tone = toneSelect ? toneSelect.value : 'professional';
        const lengthPref = lengthSelect ? lengthSelect.value : 'auto';
        savePrefs({ tone, length_preference: lengthPref });
        handleGmailGenerate(composeBox, tone, lengthPref);
      });
      // Load saved prefs into floating panel
      loadPrefs().then(res => {
        if (res.tone) {
          const tSel = panel.querySelector('.ai-tone-select');
          if (tSel) tSel.value = res.tone;
        }
        if (res.length_preference) {
          const lSel = panel.querySelector('.ai-length-select');
          if (lSel) lSel.value = res.length_preference;
        }
      });
    }
    
    console.log('[AI Draft] Button injected into compose box');
  });
}

// Map length preference keywords to approximate target word counts (int for backend)
function mapLengthPreference(pref) {
  switch (pref) {
    case 'short': return 75;
    case 'medium': return 150;
    case 'long': return 300;
    default: return null; // auto
  }
}

// Strip lines like "To:" or "Subject:" from draft body
function sanitizeDraft(draft) {
  return draft
    .split(/\r?\n/)
    .filter(line => !/^(To|Subject)\s*:/i.test(line.trim()))
    .join('\n')
    .trim();
}

// Extract logged-in Gmail user email
function getGmailUserEmail() {
  try {
    // Method 1: Check account switcher button (most reliable)
    const profileButton = document.querySelector('a[aria-label*="Google Account"], a[aria-label*="account"]');
    if (profileButton) {
      const ariaLabel = profileButton.getAttribute('aria-label');
      const emailMatch = ariaLabel?.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/);
      if (emailMatch) return emailMatch[1];
    }
    
    // Method 2: Check header area
    const emailElements = document.querySelectorAll('[email], [data-email]');
    for (const el of emailElements) {
      const email = el.getAttribute('email') || el.getAttribute('data-email');
      if (email && email.includes('@')) return email;
    }
    
    // Method 3: Check profile image area
    const profileImg = document.querySelector('img[alt][src*="googleusercontent"]');
    if (profileImg) {
      const alt = profileImg.getAttribute('alt');
      const emailMatch = alt?.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/);
      if (emailMatch) return emailMatch[1];
    }
    
    console.warn('[AI Draft] Could not detect Gmail user email');
    return null;
  } catch (e) {
    console.error('[AI Draft] Error extracting user email:', e);
    return null;
  }
}

// Extract Gmail signature from compose box
function getGmailSignature(composeBox) {
  try {
    // Method 1: Look for signature element in compose (most reliable)
    const signatureDiv = composeBox.querySelector('.gmail_signature, [data-smartmail="gmail_signature"]');
    if (signatureDiv) {
      const sigText = signatureDiv.innerText || signatureDiv.textContent;
      if (sigText && sigText.trim()) {
        console.log('[AI Draft] Signature found in compose:', sigText.substring(0, 50));
        return sigText.trim();
      }
    }
    
    // Method 2: Check for signature in compose box body (Gmail inserts it at bottom)
    const bodyField = composeBox.querySelector('[role="textbox"][aria-label*="Message"]');
    if (bodyField) {
      // Look for div with class containing 'signature'
      const sigElements = bodyField.querySelectorAll('div[class*="signature"], div[class*="gmail_signature"]');
      for (const el of sigElements) {
        const text = el.innerText || el.textContent;
        if (text && text.trim()) {
          console.log('[AI Draft] Signature found via class search:', text.substring(0, 50));
          return text.trim();
        }
      }
      
      // Method 3: Extract last section if it looks like signature (has dashes or common patterns)
      const fullText = bodyField.innerText || bodyField.textContent || '';
      const lines = fullText.split('\n');
      
      // Look for signature markers: --, Best regards, Sincerely, etc.
      const sigMarkers = ['--', 'Best regards', 'Regards', 'Sincerely', 'Thank you', 'Cheers', 'Thanks'];
      for (let i = lines.length - 10; i < lines.length; i++) {
        if (i >= 0) {
          const line = lines[i].trim();
          if (sigMarkers.some(marker => line.startsWith(marker))) {
            const signature = lines.slice(i).join('\n').trim();
            if (signature.length > 5 && signature.length < 500) {
              console.log('[AI Draft] Signature detected via pattern:', signature.substring(0, 50));
              return signature;
            }
          }
        }
      }
    }
    
    console.log('[AI Draft] No signature detected in compose');
    return null;
  } catch (e) {
    console.error('[AI Draft] Error extracting signature:', e);
    return null;
  }
}

// Handle generate click
async function handleGmailGenerate(composeBox, toneOverride, lengthPrefKeyword) {
  try {
    // Extract context from Gmail compose
    const toField = composeBox.querySelector('[name="to"]');
    const recipient = toField ? toField.value : '';
    
    const subjectField = composeBox.querySelector('[name="subjectbox"]');
    const subject = subjectField ? subjectField.value : '';
    
    const bodyField = composeBox.querySelector('[role="textbox"][aria-label*="Message"]');
    const existingText = bodyField ? bodyField.textContent.trim() : '';
    
    // Extract sender email and signature
    const senderEmail = getGmailUserEmail();
    const signature = getGmailSignature(composeBox);
    
    // Validate we have at least something
    if (!recipient && !subject && !existingText) {
      showError(composeBox, 'Please provide at least a recipient, subject, or some context in the body.');
      return;
    }
    
    // Show loading
    showLoading(composeBox);
    
    // Tone & length
    const tone = toneOverride || await getSavedTone();
    const lengthTarget = mapLengthPreference(lengthPrefKeyword);
    
    // Call API via service worker
    const response = await chrome.runtime.sendMessage({
      action: 'generateDraft',
      data: {
        recipient,
        subject,
        context: existingText,
        tone,
        length_preference: lengthTarget,
        sender_email: senderEmail,
        signature: signature
      }
    });
    
    hideLoading(composeBox);
    
    if (response.error) {
      showError(composeBox, response.error);
      return;
    }
    
    // Insert draft into compose box
    if (bodyField && response.draft) {
      bodyField.focus();
      
      // Use execCommand for better Gmail compatibility
      document.execCommand('selectAll', false, null);
      const cleaned = sanitizeDraft(response.draft);
      document.execCommand('insertText', false, cleaned);
      
      console.log('[AI Draft] Draft inserted successfully');
      showSuccess(composeBox, `Draft generated! (${cleaned.split(/\s+/).length} words, ${response.tone} tone)`);
    }
    
  } catch (error) {
    console.error('[AI Draft] Error:', error);
    hideLoading(composeBox);
    showError(composeBox, 'Failed to generate draft. Please try again.');
  }
}

// Get saved tone preference
async function getSavedTone() {
  return loadPrefs().then(p => p.tone || 'professional');
}

// Safe load prefs (chrome.storage or localStorage fallback)
function loadPrefs() {
  return new Promise((resolve) => {
    try {
      // Ask background first (preferred, avoids gmail overriding chrome object)
      chrome?.runtime?.sendMessage({ action: 'getPrefs' }, (resp) => {
        if (resp && !resp.error) {
          resolve(resp);
        } else {
          // Fallback chain
          const tone = localStorage.getItem('ai_draft_tone');
          const length_preference = localStorage.getItem('ai_draft_length');
          resolve({ tone, length_preference });
        }
      });
    } catch (e) {
      console.warn('[AI Draft] loadPrefs messaging failed, using localStorage', e);
      const tone = localStorage.getItem('ai_draft_tone');
      const length_preference = localStorage.getItem('ai_draft_length');
      resolve({ tone, length_preference });
    }
  });
}

function savePrefs(prefs) {
  try {
    // Save via background (centralizes storage access)
    chrome?.runtime?.sendMessage({ action: 'savePrefs', data: prefs }, (resp) => {
      if (resp && resp.error) {
        console.warn('[AI Draft] savePrefs background error, falling back', resp.error);
        if (prefs.tone) localStorage.setItem('ai_draft_tone', prefs.tone);
        if (prefs.length_preference) localStorage.setItem('ai_draft_length', prefs.length_preference);
      }
    });
  } catch (e) {
    console.warn('[AI Draft] savePrefs messaging failed, using localStorage', e);
    if (prefs.tone) localStorage.setItem('ai_draft_tone', prefs.tone);
    if (prefs.length_preference) localStorage.setItem('ai_draft_length', prefs.length_preference);
  }
}

// Loading UI
function showLoading(composeBox) {
  hideLoading(composeBox); // Remove any existing loader
  
  const loader = document.createElement('div');
  loader.className = 'ai-draft-loader';
  loader.innerHTML = `
    <div class="spinner"></div>
    <span>Generating draft...</span>
  `;
  composeBox.appendChild(loader);
}

function hideLoading(composeBox) {
  const loader = composeBox.querySelector('.ai-draft-loader');
  if (loader) loader.remove();
}

// Error UI
function showError(composeBox, message) {
  const errorBox = document.createElement('div');
  errorBox.className = 'ai-draft-error';
  errorBox.textContent = `❌ ${message}`;
  composeBox.appendChild(errorBox);
  
  setTimeout(() => errorBox.remove(), 5000);
}

// Success UI
function showSuccess(composeBox, message) {
  const successBox = document.createElement('div');
  successBox.className = 'ai-draft-success';
  successBox.textContent = `✅ ${message}`;
  composeBox.appendChild(successBox);
  
  setTimeout(() => successBox.remove(), 3000);
}

// Initialize
waitForGmail().then(() => {
  console.log('[AI Draft] Gmail detected, injecting button');
  injectGmailButton();
  
  // Watch for new compose boxes (Gmail is a SPA)
  const observer = new MutationObserver(() => {
    injectGmailButton();
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
});
