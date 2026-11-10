# Building Browser Extensions for Gmail & Outlook

## Overview
Browser extensions use **Manifest V3** (the latest standard) and work across Chrome, Edge, Brave, and Firefox with minimal changes.

## Project Structure
```
email-draft-extension/
├── manifest.json          # Extension configuration
├── popup/
│   ├── popup.html        # Extension popup UI
│   ├── popup.js          # Popup logic
│   └── popup.css         # Popup styles
├── content/
│   ├── gmail-content.js  # Gmail page integration
│   └── outlook-content.js # Outlook page integration
├── background/
│   └── service-worker.js # Background processes
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── utils/
    └── api.js            # Your AI API calls
```

## Step 1: Create manifest.json

```json
{
  "manifest_version": 3,
  "name": "AI Email Draft Generator",
  "version": "1.0.0",
  "description": "Generate professional email drafts with AI",
  "permissions": [
    "activeTab",
    "storage",
    "scripting"
  ],
  "host_permissions": [
    "https://mail.google.com/*",
    "https://outlook.live.com/*",
    "https://outlook.office.com/*",
    "https://outlook.office365.com/*"
  ],
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "background": {
    "service_worker": "background/service-worker.js"
  },
  "content_scripts": [
    {
      "matches": ["https://mail.google.com/*"],
      "js": ["content/gmail-content.js"],
      "css": ["content/styles.css"],
      "run_at": "document_end"
    },
    {
      "matches": [
        "https://outlook.live.com/*",
        "https://outlook.office.com/*",
        "https://outlook.office365.com/*"
      ],
      "js": ["content/outlook-content.js"],
      "css": ["content/styles.css"],
      "run_at": "document_end"
    }
  ],
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

## Step 2: Gmail Content Script

**content/gmail-content.js**
```javascript
// Wait for Gmail to load
function waitForGmail() {
  return new Promise((resolve) => {
    const checkInterval = setInterval(() => {
      // Gmail's compose box selector
      const composeBox = document.querySelector('[role="dialog"]');
      if (composeBox) {
        clearInterval(checkInterval);
        resolve();
      }
    }, 500);
  });
}

// Inject AI button into Gmail compose
function injectGmailButton() {
  // Find all compose boxes (Gmail can have multiple)
  const composeBoxes = document.querySelectorAll('[role="dialog"]');
  
  composeBoxes.forEach((composeBox) => {
    // Check if button already exists
    if (composeBox.querySelector('.ai-draft-button')) return;
    
    // Find the toolbar
    const toolbar = composeBox.querySelector('[role="toolbar"]');
    if (!toolbar) return;
    
    // Create AI button
    const aiButton = document.createElement('div');
    aiButton.className = 'ai-draft-button';
    aiButton.innerHTML = `
      <button class="ai-generate-btn" title="Generate AI Draft">
        ✨ AI Draft
      </button>
    `;
    
    // Insert button
    toolbar.appendChild(aiButton);
    
    // Add click handler
    aiButton.querySelector('.ai-generate-btn').addEventListener('click', () => {
      handleGmailGenerate(composeBox);
    });
  });
}

// Handle generate click
async function handleGmailGenerate(composeBox) {
  try {
    // Get recipient email
    const toField = composeBox.querySelector('[name="to"]');
    const recipient = toField ? toField.value : '';
    
    // Get subject
    const subjectField = composeBox.querySelector('[name="subjectbox"]');
    const subject = subjectField ? subjectField.value : '';
    
    // Get existing body text
    const bodyField = composeBox.querySelector('[role="textbox"][aria-label*="Message"]');
    const existingText = bodyField ? bodyField.textContent : '';
    
    // Show loading state
    showLoading(composeBox);
    
    // Call your AI API
    const draft = await generateDraft({
      recipient,
      subject,
      context: existingText,
      tone: await getSavedTone()
    });
    
    // Insert draft into compose box
    if (bodyField) {
      bodyField.focus();
      document.execCommand('selectAll', false, null);
      document.execCommand('insertText', false, draft);
    }
    
    hideLoading(composeBox);
    
  } catch (error) {
    console.error('AI Draft Error:', error);
    alert('Failed to generate draft. Please try again.');
    hideLoading(composeBox);
  }
}

// Generate draft using your API
async function generateDraft(params) {
  const response = await fetch('https://your-api.com/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${await getApiKey()}`
    },
    body: JSON.stringify(params)
  });
  
  const data = await response.json();
  return data.draft;
}

// Get API key from storage
async function getApiKey() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['apiKey'], (result) => {
      resolve(result.apiKey || '');
    });
  });
}

// Get saved tone preference
async function getSavedTone() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['tone'], (result) => {
      resolve(result.tone || 'professional');
    });
  });
}

// Loading UI
function showLoading(composeBox) {
  const loader = document.createElement('div');
  loader.className = 'ai-draft-loader';
  loader.innerHTML = '<div class="spinner"></div><span>Generating draft...</span>';
  composeBox.appendChild(loader);
}

function hideLoading(composeBox) {
  const loader = composeBox.querySelector('.ai-draft-loader');
  if (loader) loader.remove();
}

// Initialize
waitForGmail().then(() => {
  // Inject button initially
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
```

## Step 3: Outlook Content Script

**content/outlook-content.js**
```javascript
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
  });
}

// Inject AI button into Outlook compose
function injectOutlookButton() {
  // Find compose area
  const composeAreas = document.querySelectorAll('[role="region"][aria-label*="compose"]');
  
  composeAreas.forEach((composeArea) => {
    if (composeArea.querySelector('.ai-draft-button')) return;
    
    // Find toolbar - Outlook has different structures
    let toolbar = composeArea.querySelector('[role="toolbar"]');
    if (!toolbar) {
      toolbar = composeArea.querySelector('.ms-CommandBar');
    }
    
    if (!toolbar) return;
    
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
  });
}

// Handle generate for Outlook
async function handleOutlookGenerate(composeArea) {
  try {
    // Get recipient (Outlook uses different selectors)
    const toField = composeArea.querySelector('[aria-label*="To"]') ||
                    document.querySelector('[aria-label*="To"]');
    const recipient = toField ? toField.textContent : '';
    
    // Get subject
    const subjectField = document.querySelector('[aria-label*="Subject"]');
    const subject = subjectField ? subjectField.value || subjectField.textContent : '';
    
    // Get body editor
    const bodyField = composeArea.querySelector('[role="textbox"]') ||
                      document.querySelector('[aria-label*="Message body"]');
    const existingText = bodyField ? bodyField.textContent : '';
    
    showLoading(composeArea);
    
    const draft = await generateDraft({
      recipient,
      subject,
      context: existingText,
      tone: await getSavedTone()
    });
    
    if (bodyField) {
      bodyField.focus();
      bodyField.textContent = draft;
      // Trigger Outlook's change detection
      bodyField.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    hideLoading(composeArea);
    
  } catch (error) {
    console.error('AI Draft Error:', error);
    alert('Failed to generate draft. Please try again.');
    hideLoading(composeArea);
  }
}

// Reuse functions from Gmail (generateDraft, getApiKey, etc.)
// ... (same as Gmail content script)

// Initialize
waitForOutlook().then(() => {
  injectOutlookButton();
  
  const observer = new MutationObserver(() => {
    injectOutlookButton();
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
});
```

## Step 4: Popup UI

**popup/popup.html**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>AI Email Draft</title>
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="popup-container">
    <h2>AI Email Draft Generator</h2>
    
    <div class="settings-section">
      <label for="apiKey">API Key:</label>
      <input type="password" id="apiKey" placeholder="Enter your API key">
      
      <label for="tone">Default Tone:</label>
      <select id="tone">
        <option value="professional">Professional</option>
        <option value="friendly">Friendly</option>
        <option value="formal">Formal</option>
        <option value="casual">Casual</option>
      </select>
      
      <button id="saveBtn">Save Settings</button>
    </div>
    
    <div class="quick-generate">
      <h3>Quick Generate</h3>
      <textarea id="context" placeholder="Describe what you want to write..."></textarea>
      <button id="generateBtn">Generate Draft</button>
      <div id="result"></div>
    </div>
    
    <div class="status" id="status"></div>
  </div>
  
  <script src="popup.js"></script>
</body>
</html>
```

**popup/popup.js**
```javascript
// Load saved settings
document.addEventListener('DOMContentLoaded', async () => {
  const { apiKey, tone } = await chrome.storage.sync.get(['apiKey', 'tone']);
  
  if (apiKey) document.getElementById('apiKey').value = apiKey;
  if (tone) document.getElementById('tone').value = tone;
});

// Save settings
document.getElementById('saveBtn').addEventListener('click', async () => {
  const apiKey = document.getElementById('apiKey').value;
  const tone = document.getElementById('tone').value;
  
  await chrome.storage.sync.set({ apiKey, tone });
  
  showStatus('Settings saved!', 'success');
});

// Quick generate
document.getElementById('generateBtn').addEventListener('click', async () => {
  const context = document.getElementById('context').value;
  const resultDiv = document.getElementById('result');
  
  if (!context) {
    showStatus('Please enter a description', 'error');
    return;
  }
  
  try {
    showStatus('Generating...', 'info');
    
    const { apiKey, tone } = await chrome.storage.sync.get(['apiKey', 'tone']);
    
    const response = await fetch('https://your-api.com/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({ context, tone })
    });
    
    const data = await response.json();
    
    resultDiv.textContent = data.draft;
    resultDiv.style.display = 'block';
    
    // Add copy button
    const copyBtn = document.createElement('button');
    copyBtn.textContent = 'Copy to Clipboard';
    copyBtn.onclick = () => {
      navigator.clipboard.writeText(data.draft);
      showStatus('Copied!', 'success');
    };
    resultDiv.appendChild(copyBtn);
    
    showStatus('Generated!', 'success');
    
  } catch (error) {
    showStatus('Error generating draft', 'error');
    console.error(error);
  }
});

function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${type}`;
  setTimeout(() => status.textContent = '', 3000);
}
```

## Step 5: Styles

**content/styles.css**
```css
.ai-draft-button {
  display: inline-block;
  margin-left: 8px;
}

.ai-generate-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.ai-generate-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.ai-draft-loader {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  z-index: 10000;
  display: flex;
  align-items: center;
  gap: 12px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

## Step 6: Testing & Loading

### Local Testing

1. **Chrome/Edge:**
   - Go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select your extension folder

2. **Firefox:**
   - Go to `about:debugging#/runtime/this-firefox`
   - Click "Load Temporary Add-on"
   - Select manifest.json

3. **Test on:**
   - Gmail: mail.google.com
   - Outlook: outlook.office.com

### Debugging

```javascript
// Add console logs in content scripts
console.log('[AI Draft] Button injected');

// Check if selectors are working
console.log('Compose box:', document.querySelector('[role="dialog"]'));

// Use Chrome DevTools on the extension page
```

## Step 7: Distribution

### Chrome Web Store
1. Create developer account ($5 one-time fee)
2. Package extension as .zip
3. Upload to Chrome Web Store
4. Fill out listing details
5. Submit for review (1-3 days)

### Firefox Add-ons
1. Create Mozilla account (free)
2. Submit extension
3. Automated review + manual review
4. Usually faster than Chrome

### Edge Add-ons
1. Use same package as Chrome
2. Microsoft Partner Center account
3. Submit for review

## Advanced Features to Add

### 1. Context Menu Integration
```javascript
// In manifest.json, add:
"permissions": ["contextMenus"]

// In service-worker.js:
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "generateDraft",
    title: "Generate AI Draft",
    contexts: ["editable"]
  });
});
```

### 2. Keyboard Shortcuts
```javascript
// In manifest.json:
"commands": {
  "generate-draft": {
    "suggested_key": {
      "default": "Ctrl+Shift+G"
    },
    "description": "Generate AI draft"
  }
}
```

### 3. Analytics
```javascript
// Track usage (respect privacy!)
chrome.storage.local.get(['usageCount'], (result) => {
  const count = (result.usageCount || 0) + 1;
  chrome.storage.local.set({ usageCount: count });
});
```

### 4. Offline Support
```javascript
// Cache common templates
const templates = {
  'follow-up': 'I wanted to follow up on...',
  'meeting-request': 'I would like to schedule...'
};
```

## Security Best Practices

1. **Never store API keys in code** - always use chrome.storage
2. **Use HTTPS** for all API calls
3. **Sanitize user input** before sending to API
4. **Implement rate limiting** to prevent abuse
5. **Add content security policy** in manifest
6. **Encrypt sensitive data** in storage

## Monetization in Extensions

1. **Trial period** with API key requirement
2. **Link to subscription page** for paid plans
3. **Usage limits** enforced by backend
4. **In-extension purchases** (Chrome/Firefox support this)

## Next Steps

1. Start with Gmail support first (simpler DOM)
2. Add basic generate functionality
3. Test thoroughly with different email scenarios
4. Add Outlook support
5. Implement error handling & edge cases
6. Add analytics & user feedback
7. Submit to stores
8. Iterate based on user feedback

Would you like me to create a starter template with all these files ready to use?