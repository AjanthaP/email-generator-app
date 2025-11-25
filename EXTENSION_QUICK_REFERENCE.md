# 🚀 Extension Quick Reference

## Start Testing in 3 Steps

### 1️⃣ Start Backend
```powershell
.\start-extension-test.ps1
```
Or manually:
```powershell
uvicorn src.api.main:app --reload --port 8000
```

### 2️⃣ Load Extension
- Open: `chrome://extensions/`
- Enable "Developer mode"
- Click "Load unpacked"
- Select: `browser-extension` folder

### 3️⃣ Configure & Test
- Click extension icon
- API Key: `demo-key-001`
- Open Gmail → Compose → Click "✨ AI Draft"

---

## 📍 Key URLs

| Resource | URL |
|----------|-----|
| Backend Health | http://localhost:8000/health |
| Extension Health | http://localhost:8000/api/extension/health |
| API Docs | http://localhost:8000/docs |
| Chrome Extensions | chrome://extensions/ |
| Gmail | https://mail.google.com |
| Outlook | https://outlook.live.com |

---

## 🔑 API Keys (Staging)

| Key | User Context | Quota |
|-----|--------------|-------|
| `demo-key-001` | extension-demo-user | Unlimited |
| `test-key-staging` | staging-tester | Unlimited |

---

## 📂 Key Files

```
browser-extension/
├── manifest.json              # Extension config
├── background/
│   └── service-worker.js      # API proxy
├── content/
│   ├── gmail-content.js       # Gmail button
│   ├── outlook-content.js     # Outlook button
│   └── styles.css             # UI styles
└── popup/
    ├── popup.html             # Settings UI
    ├── popup.js               # Popup logic
    └── popup.css              # Popup styles

src/api/routers/
└── extension.py               # Backend API

docs/
├── EXTENSION_TESTING_GUIDE.md      # Detailed testing
└── EXTENSION_IMPLEMENTATION_SUMMARY.md  # Full summary
```

---

## ⚡ Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Button not appearing | Wait 5s, refresh page (CTRL+SHIFT+R) |
| API key invalid | Use `demo-key-001` in extension settings |
| Backend offline | Start server: `.\start-extension-test.ps1` |
| CORS error | Restart backend (CORS already configured) |
| Extension not loading | Check Chrome DevTools for errors |

---

## 🧪 Test Checklist

- [ ] Backend starts (check http://localhost:8000/health)
- [ ] Extension loads in Chrome
- [ ] Status shows "Connected" (green dot)
- [ ] Gmail button appears in compose
- [ ] Draft generates successfully
- [ ] Outlook button appears
- [ ] Popup quick generate works
- [ ] Usage stats display

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `EXTENSION_TESTING_GUIDE.md` | Step-by-step testing instructions |
| `EXTENSION_IMPLEMENTATION_SUMMARY.md` | Complete implementation details |
| `browser-extension/README.md` | Extension installation guide |
| `start-extension-test.ps1` | Automated startup script |

---

## 🎯 What's Next

### Immediate (Today)
1. Run `start-extension-test.ps1`
2. Load extension and configure
3. Test on Gmail and Outlook
4. Verify all features work

### Short-term (This Week)
1. Convert SVG to PNG icons (16/48/128px)
2. Deploy backend to Railway
3. Update service-worker.js with Railway URL
4. Beta test with real users

### Production (Next 1-2 Weeks)
1. Professional icon design
2. Database-backed API keys
3. Rate limiting and quotas
4. Store submission (Chrome/Firefox/Edge)

---

## 💡 Pro Tips

- Use **CTRL+SHIFT+R** to hard refresh Gmail/Outlook after loading extension
- Check **DevTools Console (F12)** for debugging info
- Service worker console: `chrome://extensions/` → Service Worker → Inspect
- Extension auto-detects compose boxes (wait 2-5 seconds after opening)
- Popup quick generate supports **CTRL+Enter** to generate

---

## ⚙️ Environment Variables

Required in `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:pass@host/db  # Optional, uses JSON if missing
```

---

## 🎨 Extension Features

✅ **One-Click Generation**: AI Draft button in Gmail/Outlook  
✅ **Smart Context**: Uses recipient, subject, body  
✅ **Tone Control**: Professional, Friendly, Formal, Casual, Enthusiastic  
✅ **Quick Generate**: From extension popup  
✅ **Usage Tracking**: Drafts today + quota  
✅ **Vector Memory**: Learns from past drafts  

---

**Version**: 1.0.0 - Staging  
**Status**: ✅ Ready for Testing  
**Updated**: November 23, 2025
