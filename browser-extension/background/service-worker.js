/**
 * Service Worker (Background Script) for AI Email Draft Extension
 * 
 * Responsibilities:
 * - Store API key securely
 * - Proxy API requests from content scripts
 * - Handle errors and retries
 * - Manage Google OAuth authentication
 */
// Diagnostics: environment info
console.log('[AI Draft][BG] Service worker starting. Version 0.1.0');
console.log('[AI Draft][BG] Sw global keys:', Object.keys(self));

// Global error handlers
self.addEventListener('error', (evt) => {
  try {
    console.error('[AI Draft][BG][GlobalError]', evt.message, 'at', evt.filename, evt.lineno, evt.colno);
  } catch (e) {
    console.error('[AI Draft][BG][GlobalError] (unparseable)', e);
  }
});

self.addEventListener('unhandledrejection', (evt) => {
  console.error('[AI Draft][BG][UnhandledPromise]', evt.reason);
});

// Default API endpoint (staging - change for production)
const API_BASE_URL = 'http://localhost:8000/api';  // Change to your Railway URL

// Cache for user profile info
let cachedUserProfile = null;

/**
 * Get user profile from backend or storage
 * Extension uses DOM extraction + backend profile lookup
 */
async function getCachedProfile() {
  try {
    // Check memory cache
    if (cachedUserProfile && cachedUserProfile.email) {
      return cachedUserProfile;
    }

    // Try to load from chrome.storage
    try {
      const stored = await chrome.storage.sync.get(['userProfile']);
      if (stored && stored.userProfile && stored.userProfile.email) {
        cachedUserProfile = stored.userProfile;
        console.log('[AI Draft][BG] Using stored profile:', cachedUserProfile.email);
        return cachedUserProfile;
      }
    } catch (e) {
      console.warn('[AI Draft][BG] Could not access storage:', e);
    }

    return null;
  } catch (error) {
    console.error('[AI Draft][BG] Error getting cached profile:', error);
    return null;
  }
}

/**
 * Save profile to cache and storage
 */
async function saveProfileCache(profile) {
  if (!profile || !profile.email) return;
  
  cachedUserProfile = profile;
  try {
    await chrome.storage.sync.set({ userProfile: profile });
    console.log('[AI Draft][BG] Profile cached:', profile.email);
  } catch (e) {
    console.warn('[AI Draft][BG] Could not save profile to storage:', e);
  }
}

/**
 * Handle messages from content scripts
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'generateDraft') {
    handleGenerateDraft(request.data)
      .then(sendResponse)
      .catch(error => sendResponse({ error: error.message }));
    return true; // Keep channel open for async response
  }
  
  if (request.action === 'checkUsage') {
    handleCheckUsage()
      .then(sendResponse)
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
  
  if (request.action === 'healthCheck') {
    handleHealthCheck()
      .then(sendResponse)
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
  if (request.action === 'getPrefs') {
    getPrefs()
      .then(sendResponse)
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
  if (request.action === 'savePrefs') {
    savePrefs(request.data)
      .then(() => sendResponse({ ok: true }))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
  if (request.action === 'getUserProfile') {
    getCachedProfile()
      .then(profile => sendResponse({ profile }))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
  if (request.action === 'saveUserProfile') {
    saveProfileCache(request.data)
      .then(() => sendResponse({ ok: true }))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
});

/**
 * Generate draft via API
 */
async function handleGenerateDraft(data) {
  const apiKey = await getApiKey();
  
  if (!apiKey) {
    throw new Error('API key not configured. Please set it in the extension popup.');
  }

  // Try to get cached profile (from storage)
  let userProfile = null;
  try {
    userProfile = await getCachedProfile();
  } catch (e) {
    console.warn('[AI Draft][BG] Could not get cached profile', e);
  }

  // Merge cached profile with extracted data (extracted data takes precedence)
  const senderEmail = data.sender_email || userProfile?.email;
  const senderName = data.sender_name || userProfile?.name || null;
  const signature = data.signature || userProfile?.signature;

  // If we got fresh data from DOM, update cache
  if (data.sender_email && data.sender_email !== userProfile?.email) {
    await saveProfileCache({
      email: data.sender_email,
      name: senderName,
      signature: signature
    });
  }

  const response = await fetch(`${API_BASE_URL}/extension/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Extension-Key': apiKey
    },
    body: JSON.stringify({
      recipient: data.recipient || null,
      subject: data.subject || null,
      body_context: data.context || null,
      tone: data.tone || 'professional',
      length_preference: data.length_preference || null,
      sender_email: senderEmail,
      sender_name: senderName,
      signature: signature
    })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error: ${response.status}`);
  }
  
  return await response.json();
}

/**
 * Check usage stats
 */
async function handleCheckUsage() {
  const apiKey = await getApiKey();
  
  if (!apiKey) {
    return { user_id: 'unknown', plan: 'none', drafts_today: 0 };
  }
  
  const response = await fetch(`${API_BASE_URL}/extension/usage`, {
    headers: {
      'X-Extension-Key': apiKey
    }
  });
  
  if (!response.ok) {
    throw new Error(`Usage check failed: ${response.status}`);
  }
  
  return await response.json();
}

/**
 * Health check
 */
async function handleHealthCheck() {
  const response = await fetch(`${API_BASE_URL}/extension/health`);
  
  if (!response.ok) {
    throw new Error('API not reachable');
  }
  
  return await response.json();
}

/**
 * Get API key from storage
 */
async function getApiKey() {
  return new Promise((resolve) => {
    try {
      chrome?.storage?.sync?.get(['apiKey'], (result) => {
        resolve((result && result.apiKey) || '');
      });
    } catch (e) {
      console.warn('[AI Draft][BG] Storage access failed for apiKey', e);
      resolve('');
    }
  });
}

/**
 * Get tone / length preferences
 */
async function getPrefs() {
  return new Promise((resolve) => {
    try {
      chrome?.storage?.sync?.get(['tone','length_preference'], (result) => {
        resolve({
          tone: (result && result.tone) || 'professional',
          length_preference: (result && result.length_preference) || 'auto'
        });
      });
    } catch (e) {
      console.warn('[AI Draft][BG] Storage access failed for prefs', e);
      resolve({ tone: 'professional', length_preference: 'auto' });
    }
  });
}

/**
 * Save tone / length preferences
 */
async function savePrefs(prefs) {
  return new Promise((resolve, reject) => {
    try {
      chrome?.storage?.sync?.set(prefs, () => resolve());
    } catch (e) {
      console.warn('[AI Draft][BG] Storage save failed, prefs:', prefs, e);
      // Fallback silently: resolve to avoid blocking UX
      resolve();
    }
  });
}

/**
 * Install event - show welcome page
 */
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('[AI Draft] Extension installed - welcome!');
    // Could open popup or onboarding page here
  }
});
