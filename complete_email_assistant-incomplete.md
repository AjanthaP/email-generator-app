# AI-Powered Email Assistant - Production-Ready Build Guide
## With Full Observability, Monitoring & Cost Control

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Day 1: Core System](#day-1-core-system)
5. [Day 2: Advanced Features](#day-2-advanced-features)
6. [Day 3: Monitoring & Polish](#day-3-monitoring--polish)
7. [Production Deployment](#production-deployment)
8. [Real-World Monetization](#real-world-monetization)

---

## 🎯 Project Overview

**Goal:** Build a production-ready, monitored multi-agent email assistant that's ready for real-world deployment.

**Key Features:**
- ✅ 7 specialized agents with distinct roles
- ✅ LangGraph workflow orchestration
- ✅ **LangSmith tracing & monitoring**
- ✅ **Token counting & cost tracking**
- ✅ **Rate limiting & quotas**
- ✅ Multi-tone support (formal, casual, assertive, empathetic)
- ✅ Memory/personalization system
- ✅ **Quality scoring engine**
- ✅ **A/B testing capabilities**
- ✅ **Analytics dashboard**
- ✅ Template library
- ✅ Export functionality (TXT, MD, HTML)

**Tech Stack:**
- **LLM:** Google Gemini 2.0 Flash (free tier: 60 req/min)
- **Framework:** LangChain + LangGraph
- **Monitoring:** LangSmith (optional) + Custom metrics
- **UI:** Streamlit
- **Memory:** JSON files
- **Python:** 3.10+

**Real-World Value:**
- SaaS potential: $10-50/user/month
- Market: Sales teams, recruiters, executives, support teams
- Similar products: Lavender.ai ($29-99/mo), Flowrite ($5-15/mo)

---

## 📊 Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                       Streamlit UI                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Compose  │  │Templates │  │ History  │  │Analytics │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Monitoring Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │LangSmith │  │  Tokens  │  │   Cost   │  │   Rate   │  │
│  │ Tracing  │  │ Counter  │  │ Tracker  │  │ Limiter  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Workflow Engine                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Agent Layer                               │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐           │
│  │ Input  │→ │ Intent │→ │ Draft  │→ │  Tone  │           │
│  │ Parser │  │Detector│  │ Writer │  │Stylist │           │
│  └────────┘  └────────┘  └────────┘  └────────┘           │
│                     ↓                                        │
│  ┌────────┐  ┌────────┐  ┌────────┐                       │
│  │Personal│→ │ Review │→ │ Router │                       │
│  │ -ization│  │ Agent  │  │ Agent  │                       │
│  └────────┘  └────────┘  └────────┘                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Memory & Storage                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  User    │  │  Draft   │  │ Metrics  │                 │
│  │ Profiles │  │ History  │  │   Log    │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
```bash
# System requirements
Python 3.10 or higher
pip (latest version)
Git

# API Keys needed
1. Google Gemini API Key (free tier)
   → Get from: https://makersuite.google.com/app/apikey
   
2. LangSmith API Key (optional, free tier)
   → Get from: https://smith.langchain.com/
```

### Installation (5 minutes)
```bash
# 1. Create project
mkdir email_assistant
cd email_assistant

# 2. Set up virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 3. Create requirements.txt
cat > requirements.txt << 'EOF'
# Core LLM Framework
langchain==0.1.20
langchain-google-genai==1.0.1
langgraph==0.0.55
google-generativeai==0.4.0

# Monitoring & Tracing
langsmith==0.1.0
tiktoken==0.6.0

# Web Interface
streamlit==1.31.0
plotly==5.18.0

# Configuration
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Testing
pytest==7.4.4
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code Quality
black==24.1.0
flake8==7.0.0

# Utilities
pandas==2.2.0
EOF

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create environment file
cat > .env << 'EOF'
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# LangSmith (Optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=email-assistant-prod
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Application Settings
APP_NAME=AI Email Assistant
DEBUG=true
LOG_LEVEL=INFO

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60
DAILY_COST_LIMIT=1.0

# LLM Settings
MAX_TOKENS=2000
TEMPERATURE=0.7
EOF

# 6. Create .env.example (for Git)
cp .env .env.example
sed -i 's/=.*/=your_key_here/g' .env.example
```

---

## 📁 Project Structure

```bash
# Create complete directory structure
mkdir -p src/{agents,workflow,memory,utils,ui}
mkdir -p tests
mkdir -p data/templates
mkdir -p docs
mkdir -p dashboards

# Create __init__.py files
touch src/__init__.py
touch src/agents/__init__.py
touch src/workflow/__init__.py
touch src/memory/__init__.py
touch src/utils/__init__.py
touch tests/__init__.py

# Final structure:
email_assistant/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── input_parser.py
│   │   ├── intent_detector.py
│   │   ├── draft_writer.py
│   │   ├── tone_stylist.py
│   │   ├── personalization.py
│   │   ├── review_agent.py
│   │   ├── quality_scorer.py         # ⭐ NEW
│   │   ├── ab_testing.py             # ⭐ NEW
│   │   └── router.py
│   ├── workflow/
│   │   ├── __init__.py
│   │   └── langgraph_flow.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── user_profiles.json
│   │   ├── draft_history.json
│   │   ├── metrics.json              # ⭐ NEW
│   │   └── memory_manager.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── monitoring.py             # ⭐ NEW
│   │   ├── rate_limiter.py           # ⭐ NEW
│   │   ├── token_counter.py          # ⭐ NEW
│   │   ├── template_engine.py        # ⭐ NEW
│   │   └── validators.py
│   └── ui/
│       └── streamlit_app.py
├── dashboards/
│   └── analytics_dashboard.py        # ⭐ NEW
├── tests/
│   ├── test_agents.py
│   ├── test_workflow.py
│   ├── test_monitoring.py            # ⭐ NEW
│   └── test_integration.py
├── data/
│   └── templates/
│       ├── outreach.json
│       ├── followup.json
│       └── thankyou.json
├── docs/
│   ├── architecture.md
│   └── api_documentation.md
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── setup.py
```

---

## 🚀 Day 1: Core System (8-10 hours)

### Hour 1: Configuration & Monitoring Setup

#### Create `src/utils/config.py`
```python
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application configuration"""
    
    # API Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # LangSmith Configuration
    langchain_tracing_v2: bool = True
    langchain_api_key: Optional[str] = None
    langchain_project: str = "email-assistant-prod"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    
    # Application Settings
    app_name: str = "AI Email Assistant"
    debug: bool = False
    log_level: str = "INFO"
    
    # Rate Limiting
    max_requests_per_minute: int = 60
    daily_cost_limit: float = 1.0
    
    # LLM Settings
    max_tokens: int = 2000
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Set LangSmith environment variables
if settings.langchain_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2)
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
```

#### Create `src/utils/token_counter.py`
```python
import tiktoken
from typing import Dict

class TokenCounter:
    """Count tokens and estimate costs"""
    
    def __init__(self, model: str = "gpt-4"):
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except:
            # Fallback to cl100k_base (GPT-4/GPT-3.5-turbo encoding)
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Pricing per 1M tokens (example for Gemini 2.0 Flash)
        self.pricing = {
            "input_per_1m": 0.075,   # $0.075 per 1M input tokens
            "output_per_1m": 0.30     # $0.30 per 1M output tokens
        }
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def count_messages_tokens(self, messages: list) -> int:
        """Count tokens in chat messages"""
        total = 0
        for message in messages:
            if isinstance(message, dict):
                total += self.count_tokens(str(message.get('content', '')))
            else:
                total += self.count_tokens(str(message))
        return total
    
    def estimate_cost(self, 
                     input_tokens: int, 
                     output_tokens: int) -> float:
        """Estimate cost in USD"""
        input_cost = (input_tokens / 1_000_000) * self.pricing["input_per_1m"]
        output_cost = (output_tokens / 1_000_000) * self.pricing["output_per_1m"]
        return input_cost + output_cost
    
    def get_token_breakdown(self, 
                           input_text: str, 
                           output_text: str) -> Dict:
        """Get detailed token breakdown"""
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        total_tokens = input_tokens + output_tokens
        cost = self.estimate_cost(input_tokens, output_tokens)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": round(cost, 6),
            "cost_formatted": f"${cost:.6f}"
        }
```

#### Create `src/utils/rate_limiter.py`
```python
import time
from collections import deque
from typing import Optional, Tuple
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiting and cost control"""
    
    def __init__(self, 
                 max_requests_per_minute: int = 60,
                 daily_cost_limit: float = 1.0):
        self.max_requests = max_requests_per_minute
        self.time_window = 60  # seconds
        self.daily_cost_limit = daily_cost_limit
        
        # Track requests in sliding window
        self.requests = deque()
        
        # Track daily cost
        self.current_cost = 0.0
        self.last_reset = datetime.now().date()
    
    def _reset_if_new_day(self):
        """Reset daily counters if it's a new day"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.current_cost = 0.0
            self.last_reset = today
    
    def can_make_request(self) -> Tuple[bool, Optional[str]]:
        """Check if request is allowed"""
        self._reset_if_new_day()
        now = time.time()
        
        # Remove old requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # Check rate limit
        if len(self.requests) >= self.max_requests:
            wait_time = self.time_window - (now - self.requests[0])
            return False, f"⏳ Rate limit exceeded. Wait {wait_time:.1f}s"
        
        # Check cost limit
        if self.current_cost >= self.daily_cost_limit:
            return False, f"💰 Daily cost limit reached (${self.daily_cost_limit:.2f}). Resets tomorrow."
        
        return True, None
    
    def record_request(self, cost: float = 0.0):
        """Record a request and its cost"""
        self.requests.append(time.time())
        self.current_cost += cost
    
    def get_stats(self) -> dict:
        """Get current rate limiter stats"""
        now = time.time()
        
        # Clean old requests
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        return {
            "requests_in_window": len(self.requests),
            "max_requests": self.max_requests,
            "requests_remaining": self.max_requests - len(self.requests),
            "current_cost_today": round(self.current_cost, 4),
            "daily_limit": self.daily_cost_limit,
            "cost_remaining": round(self.daily_cost_limit - self.current_cost, 4)
        }
```

#### Create `src/utils/monitoring.py`
```python
import os
import json
import time
from datetime import datetime
from typing import Dict, Optional
from langsmith import Client
from langsmith.run_helpers import traceable

class MonitoringManager:
    """Comprehensive monitoring with LangSmith integration"""
    
    def __init__(self):
        # Initialize LangSmith client if API key is available
        self.langsmith_enabled = bool(os.getenv("LANGCHAIN_API_KEY"))
        self.client = Client() if self.langsmith_enabled else None
        
        # Local metrics storage
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "avg_latency": 0.0,
            "requests_by_intent": {},
            "requests_by_tone": {},
            "error_types": {},
            "daily_stats": {},
            "quality_scores": []
        }
        
        self.metrics_file = "src/memory/metrics.json"
        self._load_metrics()
    
    def _load_metrics(self):
        """Load metrics from file"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    loaded = json.load(f)
                    self.metrics.update(loaded)
        except Exception as e:
            print(f"Warning: Could not load metrics: {e}")
    
    def _save_metrics(self):
        """Save metrics to file"""
        try:
            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save metrics: {e}")
    
    @traceable(name="email_generation", run_type="chain")
    def track_request(self,
                     intent: str,
                     tone: str,
                     success: bool,
                     latency: float,
                     input_tokens: int = 0,
                     output_tokens: int = 0,
                     cost: float = 0.0,
                     quality_score: Optional[float] = None,
                     error: Optional[str] = None,
                     metadata: Optional[Dict] = None):
        """Track individual request with full details"""
        
        # Get current date for daily tracking
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.metrics["daily_stats"]:
            self.metrics["daily_stats"][today] = {
                "requests": 0,
                "cost": 0.0,
                "tokens": 0
            }
        
        # Update counters
        self.metrics["total_requests"] += 1
        self.metrics["daily_stats"][today]["requests"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
            if error:
                error_type = error.split(':')[0] if ':' in error else error
                self.metrics["error_types"][error_type] = \
                    self.metrics["error_types"].get(error_type, 0) + 1
        
        # Track tokens
        total_tokens = input_tokens + output_tokens
        self.metrics["total_tokens"] += total_tokens
        self.metrics["total_input_tokens"] += input_tokens
        self.metrics["total_output_tokens"] += output_tokens
        self.metrics["daily_stats"][today]["tokens"] += total_tokens
        
        # Track cost
        self.metrics["total_cost"] += cost
        self.metrics["daily_stats"][today]["cost"] += cost
        
        # Track by intent and tone
        self.metrics["requests_by_intent"][intent] = \
            self.metrics["requests_by_intent"].get(intent, 0) + 1
        self.metrics["requests_by_tone"][tone] = \
            self.metrics["requests_by_tone"].get(tone, 0) + 1
        
        # Update average latency
        total = self.metrics["total_requests"]
        current_avg = self.metrics["avg_latency"]
        self.metrics["avg_latency"] = \
            ((current_avg * (total - 1)) + latency) / total
        
        # Track quality scores
        if quality_score is not None:
            self.metrics["quality_scores"].append({
                "score": quality_score,
                "timestamp": datetime.now().isoformat(),
                "intent": intent,
                "tone": tone
            })
            # Keep only last 100 scores
            self.metrics["quality_scores"] = self.metrics["quality_scores"][-100:]
        
        # Save to file
        self._save_metrics()
        
        # Send to LangSmith if available
        if self.client and success:
            try:
                self.client.create_feedback(
                    key="request_metrics",
                    score=quality_score if quality_score else 1.0,
                    value={
                        "intent": intent,
                        "tone": tone,
                        "latency": latency,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cost": cost,
                        **(metadata or {})
                    }
                )
            except Exception as e:
                print(f"Warning: Could not send to LangSmith: {e}")
    
    def get_metrics_summary(self) -> Dict:
        """Get comprehensive metrics summary"""
        success_rate = 0.0
        if self.metrics["total_requests"] > 0:
            success_rate = (self.metrics["successful_requests"] / 
                           self.metrics["total_requests"]) * 100
        
        # Calculate average quality score
        avg_quality = 0.0
        if self.metrics["quality_scores"]:
            avg_quality = sum(s["score"] for s in self.metrics["quality_scores"]) / \
                         len(self.metrics["quality_scores"])
        
        # Get today's stats
        today = datetime.now().strftime("%Y-%m-%d")
        today_stats = self.metrics["daily_stats"].get(today, {
            "requests": 0,
            "cost": 0.0,
            "tokens": 0
        })
        
        return {
            "total_requests": self.metrics["total_requests"],
            "success_rate": f"{success_rate:.2f}%",
            "total_cost": f"${self.metrics['total_cost']:.4f}",
            "total_tokens": self.metrics["total_tokens"],
            "input_tokens": self.metrics["total_input_tokens"],
            "output_tokens": self.metrics["total_output_tokens"],
            "avg_latency": f"{self.metrics['avg_latency']:.2f}s",
            "avg_quality_score": f"{avg_quality:.2f}",
            "by_intent": self.metrics["requests_by_intent"],
            "by_tone": self.metrics["requests_by_tone"],
            "errors": self.metrics["error_types"],
            "today": {
                "requests": today_stats["requests"],
                "cost": f"${today_stats['cost']:.4f}",
                "tokens": today_stats["tokens"]
            },
            "langsmith_enabled": self.langsmith_enabled
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "avg_latency": 0.0,
            "requests_by_intent": {},
            "requests_by_tone": {},
            "error_types": {},
            "daily_stats": {},
            "quality_scores": []
        }
        self._save_metrics()
    
    def export_metrics(self, filepath: str):
        """Export metrics to file"""
        with open(filepath, 'w') as f:
            json.dump(self.metrics, f, indent=2)
```

### Hour 2-3: Core Agents

#### `src/agents/input_parser.py` (Same as before)
#### `src/agents/intent_detector.py` (Same as before)
#### `src/agents/draft_writer.py` (Same as before)

*[Use code from previous artifact - keeping same for brevity]*

### Hour 3-5: Quality Scorer & Enhanced Workflow

#### Create `src/agents/quality_scorer.py`
```python
from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

class QualityScorer:
    """Score email quality on multiple dimensions"""
    
    def __init__(self, llm):
        self.llm = llm
        self.scoring_prompt = ChatPromptTemplate.from_template("""
        You are an expert email quality analyst. Score this email on a scale of 0-10 for each criterion.
        
        Email Draft:
        {draft}
        
        Expected Tone: {tone}
        Expected Intent: {intent}
        
        Rate on these criteria (0-10 scale):
        1. CLARITY: Is the message clear and easy to understand?
        2. CONCISENESS: Is it appropriately brief without unnecessary words?
        3. TONE_MATCH: Does it match the expected tone ({tone})?
        4. GRAMMAR: Is it grammatically correct?
        5. ACTIONABILITY: Does it have clear next steps/call-to-action?
        6. PROFESSIONALISM: Is it polished and professional?
        
        Return ONLY a JSON object with scores:
        {{
          "clarity": <score>,
          "conciseness": <score>,
          "tone_match": <score>,
          "grammar": <score>,
          "actionability": <score>,
          "professionalism": <score>
        }}
        """)
    
    def score_email(self, draft: str, intent: str, tone: str) -> Dict:
        """Comprehensive quality scoring"""
        try:
            # Get LLM scores
            chain = self.scoring_prompt | self.llm
            response = chain.invoke({
                "draft": draft,
                "tone": tone,
                "intent": intent
            })
            
            # Parse JSON response
            import json
            import re
            content = response.content
            
            # Extract JSON from markdown blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            scores = json.loads(content.strip())
            
            # Normalize to 0-1 scale
            normalized_scores = {k: v/10 for k, v in scores.items()}
            
            # Calculate weighted overall score
            weights = {
                "clarity": 0.20,
                "conciseness": 0.15,
                "tone_match": 0.25,
                "grammar": 0.15,
                "actionability": 0.15,
                "professionalism": 0.10
            }
            
            overall = sum(normalized_scores.get(k, 0.5) * weights[k] for k in weights)
            
            # Add quick validation checks
            quick_checks = self._quick_validation(draft)
            
            return {
                "overall_score": round(overall, 2),
                "grade": self._get_grade(overall),
                "breakdown": normalized_scores,
                "quick_checks": quick_checks,
                "recommendations": self._get_recommendations(normalized_scores, quick_checks)
            }
            
        except Exception as e:
            print(f"Error scoring email: {e}")
            # Return default scores
            return {
                "overall_score": 0.7,
                "grade": "B",
                "breakdown": {
                    "clarity": 0.7,
                    "conciseness": 0.7,
                    "tone_match": 0.7,
                    "grammar": 0.7,
                    "actionability": 0.7,
                    "professionalism": 0.7
                },
                "quick_checks": self._quick_validation(draft),
                "recommendations": []
            }
    
    def _quick_validation(self, draft: str) -> Dict:
        """Quick validation checks"""
        issues = []
        
        # Length check
        word_count = len(draft.split())
        if word_count < 30:
            issues.append("Email may be too short")
        elif word_count > 300:
            issues.append("Email may be too long")
        
        # Greeting check
        greetings = ["dear", "hi", "hello", "hey"]
        has_greeting = any(g in draft.lower()[:50] for g in greetings)
        
        # Closing check
        closings = ["regards", "sincerely", "best", "thanks", "cheers"]
        has_closing = any(c in draft.lower()[-100:] for c in closings)
        
        # Exclamation marks
        if draft.count("!") > 2:
            issues.append("Too many exclamation marks")
        
        # Check for question
        has_question = "?" in draft
        
        return {
            "word_count": word_count,
            "has_greeting": has_greeting,
            "has_closing": has_closing,
            "has_question": has_question,
            "exclamation_count": draft.count("!"),
            "issues": issues
        }
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 0.93: return "A+"
        elif score >= 0.90: return "A"
        elif score >= 0.87: return "A-"
        elif score >= 0.83: return "B+"
        elif score >= 0.80: return "B"
        elif score >= 0.77: return "B-"
        elif score >= 0.73: return "C+"
        elif score >= 0.70: return "C"
        else: return "C-"
    
    def _get_recommendations(self, scores: Dict, checks: Dict) -> list:
        """Generate improvement recommendations"""
        recommendations = []
        
        if scores.get("clarity", 1) < 0.7:
            recommendations.append("💡 Simplify sentence structure for better clarity")
        
        if scores.get("conciseness", 1) < 0.7:
            recommendations.append("✂️ Remove unnecessary words and phrases")
        
        if scores.get("tone_match", 1) < 0.7:
            recommendations.append("🎭 Adjust language to better match desired tone")
        
        if scores.get("grammar", 1) < 0.8:
            recommendations.append("📝 Review for grammatical errors")
        
        if scores.get("actionability", 1) < 0.7:
            recommendations.append("🎯 Add a clear call-to-action")
        
        if not checks.get("has_greeting"):
            recommendations.append("👋 Add a proper greeting")
        
        if not checks.get("has_closing"):
            recommendations.append("✍️ Add a professional closing")
        
        if checks.get("word_count", 0) > 250:
            recommendations.append("📏 Consider making the email more concise")
        
        return recommendations
```

### Hour 5-7: Enhanced Workflow with Monitoring

#### Update `src/workflow/langgraph_flow.py`
```python
from typing import TypedDict, Dict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
import time

from src.agents.input_parser import InputParserAgent
from src.agents.intent_detector import IntentDetectorAgent
from src.agents.draft_writer import DraftWriterAgent
from src.agents.tone_stylist import ToneStylistAgent
from src.agents.personalization import PersonalizationAgent
from src.agents.review_agent import ReviewAgent
from src.agents.quality_scorer import QualityScorer
from src.agents.router import RouterAgent

from src.utils.config import settings
from src.utils.monitoring import MonitoringManager
from src.utils.token_counter import TokenCounter
from src.utils.rate_limiter import RateLimiter

# Initialize global instances
monitor = MonitoringManager()
token_counter = TokenCounter()
rate_limiter = RateLimiter(
    max_requests_per_minute=settings.max_requests_per_minute,
    daily_cost_limit=settings.daily_cost_limit
)

class EmailState(TypedDict):
    """Enhanced state with monitoring"""
    # Input
    user_input: str
    tone: str
    user_id: str
    
    # Parsed data
    parsed_data: dict
    recipient: str
    intent_hint: str
    
    # Processing
    intent: str
    draft: str
    styled_draft: str
    personalized_draft: str
    
    # Quality
    quality_score: dict
    
    # Output
    final_draft: str
    metadata: dict
    
    # Monitoring
    start_time: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    
    # Control flow
    error: str
    retry_count: int
    needs_improvement: bool

def create_email_workflow():
    """Create enhanced workflow with monitoring"""
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=settings.temperature,
        max_output_tokens=settings.max_tokens
    )
    
    # Initialize agents
    input_parser = InputParserAgent(llm)
    intent_detector = IntentDetectorAgent(llm)
    draft_writer = DraftWriterAgent(llm)
    tone_stylist = ToneStylistAgent(llm)
    personalization_agent = PersonalizationAgent(llm)
    review_agent = ReviewAgent(llm)
    quality_scorer = QualityScorer(llm)
    router = RouterAgent(llm)
    
    # Wrap agents with token counting
    def counted_input_parser(state: Dict) -> Dict:
        """Input parser with token counting"""
        input_text = state["user_input"]
        input_tokens = token_counter.count_tokens(input_text)
        
        result = input_parser(state)
        
        output_text = str(result.get("parsed_data", {}))
        output_tokens = token_counter.count_tokens(output_text)
        
        return {
            **result,
            "input_tokens": state.get("input_tokens", 0) + input_tokens,
            "output_tokens": state.get("output_tokens", 0) + output_tokens
        }
    
    def counted_draft_writer(state: Dict) -> Dict:
        """Draft writer with token counting"""
        input_text = str(state.get("parsed_data", {}))
        input_tokens = token_counter.count_tokens(input_text)
        
        result = draft_writer(state)
        
        output_text = result.get("draft", "")
        output_tokens = token_counter.count_tokens(output_text)
        
        return {
            **result,
            "input_tokens": state.get("input_tokens", 0) + input_tokens,
            "output_tokens": state.get("output_tokens", 0) + output_tokens
        }
    
    def score_quality(state: Dict) -> Dict:
        """Score email quality"""
        draft = state.get("personalized_draft", state.get("draft", ""))
        intent = state.get("intent", "outreach")
        tone = state.get("tone", "formal")
        
        quality_score = quality_scorer.score_email(draft, intent, tone)
        
        return {"quality_score": quality_score}
    
    # Define workflow
    workflow = StateGraph(EmailState)
    
    # Add nodes with monitoring
    workflow.add_node("parse_input", counted_input_parser)
    workflow.add_node("detect_intent", intent_detector)
    workflow.add_node("write_draft", counted_draft_writer)
    workflow.add_node("adjust_tone", tone_stylist)
    workflow.add_node("personalize", personalization_agent)
    workflow.add_node("review", review_agent)
    workflow.add_node("score_quality", score_quality)
    
    # Define edges
    workflow.add_edge("parse_input", "detect_intent")
    workflow.add_edge("detect_intent", "write_draft")
    workflow.add_edge("write_draft", "adjust_tone")
    workflow.add_edge("adjust_tone", "personalize")
    workflow.add_edge("personalize", "review")
    workflow.add_edge("review", "score_quality")
    workflow.add_edge("score_quality", END)
    
    # Set entry point
    workflow.set_entry_point("parse_input")
    
    return workflow.compile()

def generate_email(user_input: str, 
                  tone: str = "formal", 
                  user_id: str = "default") -> Dict:
    """Generate email with full monitoring"""
    
    # Check rate limits
    can_proceed, error_msg = rate_limiter.can_make_request()
    if not can_proceed:
        return {
            "error": error_msg,
            "final_draft": "",
            "rate_limited": True
        }
    
    # Start timing
    start_time = time.time()
    
    # Initialize workflow
    workflow = create_email_workflow()
    
    initial_state = {
        "user_input": user_input,
        "tone": tone,
        "user_id": user_id,
        "retry_count": 0,
        "needs_improvement": False,
        "start_time": start_time,
        "input_tokens": 0,
        "output_tokens": 0
    }
    
    try:
        # Run workflow
        result = workflow.invoke(initial_state)
        
        # Calculate metrics
        latency = time.time() - start_time
        input_tokens = result.get("input_tokens", 0)
        output_tokens = result.get("output_tokens", 0)
        total_tokens = input_tokens + output_tokens
        cost = token_counter.estimate_cost(input_tokens, output_tokens)
        
        # Get quality score
        quality_score = result.get("quality_score", {})
        overall_quality = quality_score.get("overall_score", 0.7)
        
        # Record request
        rate_limiter.record_request(cost)
        
        # Track in monitoring
        monitor.track_request(
            intent=result.get("intent", "unknown"),
            tone=tone,
            success=True,
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            quality_score=overall_quality,
            metadata={
                "user_id": user_id,
                "grade": quality_score.get("grade", "N/A")
            }
        )
        
        # Add monitoring data to result
        result["monitoring"] = {
            "latency": f"{latency:.2f}s",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": f"${cost:.6f}",
            "quality_score": overall_quality,
            "grade": quality_score.get("grade", "N/A")
        }
        
        return result
        
    except Exception as e:
        # Track error
        latency = time.time() - start_time
        monitor.track_request(
            intent="unknown",
            tone=tone,
            success=False,
            latency=latency,
            error=str(e)
        )
        
        return {
            "error": str(e),
            "final_draft": "An error occurred. Please try again.",
            "monitoring": {
                "latency": f"{latency:.2f}s",
                "error": str(e)
            }
        }
```

### Hour 7-8: Enhanced Streamlit UI with Monitoring

#### Update `src/ui/streamlit_app.py`
```python
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.workflow.langgraph_flow import generate_email, monitor, rate_limiter
from src.memory.memory_manager import MemoryManager

# Initialize
memory = MemoryManager()

# Page config
st.set_page_config(
    page_title="AI Email Assistant Pro",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .quality-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }
    .grade-a { background-color: #4CAF50; color: white; }
    .grade-b { background-color: #2196F3; color: white; }
    .grade-c { background-color: #FF9800; color: white; }
</style>
""", unsafe_allow_html=True)

# Header
st.title("✉️ AI Email Assistant Pro")
st.markdown("*Production-ready email generation with full observability*")

# Sidebar - Configuration & Monitoring
st.sidebar.header("⚙️ Configuration")

user_id = st.sidebar.text_input("User ID", value="default")
tone = st.sidebar.selectbox(
    "Email Tone",
    ["formal", "casual", "assertive", "empathetic"],
    help="Choose the tone for your email"
)

# Monitoring Dashboard in Sidebar
st.sidebar.markdown("---")
st.sidebar.header("📊 Monitoring Dashboard")

metrics = monitor.get_metrics_summary()
rate_stats = rate_limiter.get_stats()

# Display key metrics
col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("Requests", metrics["total_requests"])
    st.metric("Success Rate", metrics["success_rate"])
with col2:
    st.metric("Total Cost", metrics["total_cost"])
    st.metric("Avg Latency", metrics["avg_latency"])

# Rate limiter status
st.sidebar.markdown("### Rate Limiter Status")
st.sidebar.progress(rate_stats["requests_in_window"] / rate_stats["max_requests"])
st.sidebar.caption(f"{rate_stats['requests_remaining']} requests remaining this minute")

st.sidebar.progress(
    (rate_stats["daily_limit"] - rate_stats["cost_remaining"]) / rate_stats["daily_limit"]
)
st.sidebar.caption(f"${rate_stats['cost_remaining']:.4f} cost remaining today")

# LangSmith status
if metrics["langsmith_enabled"]:
    st.sidebar.success("✅ LangSmith Tracing Active")
else:
    st.sidebar.warning("⚠️ LangSmith Disabled")

# Advanced settings
with st.sidebar.expander("⚙️ Advanced Settings"):
    show_metadata = st.checkbox("Show metadata", value=True)
    show_quality_score = st.checkbox("Show quality score", value=True)
    save_to_history = st.checkbox("Save to history", value=True)
    
    if st.button("Reset Metrics"):
        monitor.reset_metrics()
        st.success("Metrics reset!")
        st.rerun()

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "✍️ Compose", 
    "📝 Templates", 
    "📚 History", 
    "📊 Analytics"
])

# TAB 1: Compose
with tab1:
    st.header("📝 Compose Your Email")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        user_prompt = st.text_area(
            "Describe your email:",
            placeholder="Example: Write a follow-up email to John Smith from TechCorp thanking him for yesterday's meeting and proposing next steps...",
            height=200,
            key="compose_prompt"
        )
        
        recipient = st.text_input(
            "Recipient Name (optional):",
            placeholder="John Smith"
        )
        
        generate_btn = st.button("✨ Generate Email", type="primary", use_container_width=True)
    
    with col2:
        st.info("💡 **Tips for best results:**\n\n"
                "- Be specific about the email purpose\n"
                "- Mention key points to include\n"
                "- Specify recipient's role/company\n"
                "- Include relevant context")
        
        # Show current rate limit status
        st.markdown("### ⚡ Current Status")
        st.metric("Requests Available", rate_stats["requests_remaining"])
        st.metric("Cost Budget Remaining", f"${rate_stats['cost_remaining']:.4f}")
    
    # Generate email
    if generate_btn:
        if not user_prompt:
            st.error("⚠️ Please describe your email request")
        else:
            with st.spinner("🤖 Crafting your email..."):
                # Add recipient to prompt
                full_prompt = user_prompt
                if recipient:
                    full_prompt = f"Recipient: {recipient}\n\n{user_prompt}"
                
                # Generate
                result = generate_email(full_prompt, tone, user_id)
                
                # Check for rate limit
                if result.get("rate_limited"):
                    st.error(f"🚫 {result['error']}")
                elif result.get("error"):
                    st.error(f"❌ Error: {result['error']}")
                else:
                    # Store in session
                    st.session_state['last_draft'] = result.get('final_draft', result.get('draft', ''))
                    st.session_state['last_metadata'] = {
                        'intent': result.get('intent', 'N/A'),
                        'recipient': result.get('recipient', recipient),
                        'tone': tone,
                        'monitoring': result.get('monitoring', {}),
                        'quality_score': result.get('quality_score', {}),
                        'original_prompt': user_prompt
                    }
                    
                    # Save to history
                    if save_to_history:
                        memory.save_draft(user_id, {
                            'prompt': user_prompt,
                            'draft': st.session_state['last_draft'],
                            'tone': tone,
                            'intent': result.get('intent', 'N/A'),
                            'quality_score': result.get('quality_score', {}).get('overall_score', 0.7)
                        })
                    
                    st.success("✅ Email generated successfully!")
    
    # Display result
    if 'last_draft' in st.session_state:
        st.markdown("---")
        st.header("📧 Your Email Draft")
        
        metadata = st.session_state.get('last_metadata', {})
        monitoring = metadata.get('monitoring', {})
        quality_score = metadata.get('quality_score', {})
        
        # Metrics row
        if show_metadata:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("📋 Intent", metadata.get('intent', 'N/A').replace('_', ' ').title())
            with col2:
                st.metric("🎭 Tone", metadata.get('tone', 'N/A').title())
            with col3:
                st.metric("⚡ Latency", monitoring.get('latency', 'N/A'))
            with col4:
                st.metric("🪙 Tokens", monitoring.get('total_tokens', 'N/A'))
            with col5:
                st.metric("💰 Cost", monitoring.get('estimated_cost', 'N/A'))
        
        # Quality score
        if show_quality_score and quality_score:
            st.markdown("### 🎯 Quality Analysis")
            
            col1, col2, col3 = st.columns([1, 2, 2])
            
            with col1:
                grade = quality_score.get('grade', 'B')
                grade_class = f"grade-{grade[0].lower()}"
                overall = quality_score.get('overall_score', 0.7)
                
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <h2>Overall Grade</h2>
                    <div class="quality-badge {grade_class}" style="font-size: 48px; margin: 20px 0;">
                        {grade}
                    </div>
                    <p style="font-size: 24px;">{overall:.2f}/1.00</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Breakdown scores
                breakdown = quality_score.get('breakdown', {})
                st.markdown("#### Score Breakdown")
                for criterion, score in breakdown.items():
                    st.progress(score)
                    st.caption(f"{criterion.replace('_', ' ').title()}: {score:.2f}")
            
            with col3:
                # Recommendations
                recommendations = quality_score.get('recommendations', [])
                if recommendations:
                    st.markdown("#### 💡 Recommendations")
                    for rec in recommendations:
                        st.markdown(f"- {rec}")
                else:
                    st.success("✅ No improvements needed!")
        
        # Editable draft
        edited_draft = st.text_area(
            "Edit your email:",
            value=st.session_state['last_draft'],
            height=350,
            key="email_editor"
        )
        
        # Stats
        word_count = len(edited_draft.split())
        char_count = len(edited_draft)
        st.caption(f"📊 {word_count} words • {char_count} characters")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.download_button(
                "📥 Download TXT",
                edited_draft,
                file_name=f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                "📄 Download MD",
                edited_draft,
                file_name=f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col3:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.code(edited_draft, language=None)
                st.success("✅ Select text above to copy!")
        
        with col4:
            if st.button("🔄 Generate New", use_container_width=True):
                # Learn from edits
                if edited_draft != st.session_state['last_draft']:
                    memory.learn_from_edits(user_id, st.session_state['last_draft'], edited_draft)
                
                del st.session_state['last_draft']
                st.rerun()

# TAB 2: Templates
with tab2:
    st.header("📝 Email Templates")
    st.markdown("Quick start with pre-built templates")
    
    templates = {
        "Cold Outreach": {
            "prompt": "Write a cold outreach email to a potential client introducing our AI consulting services that help companies implement intelligent automation",
            "tone": "formal",
            "description": "Professional introduction to prospects",
            "icon": "🎯"
        },
        "Meeting Follow-up": {
            "prompt": "Write a follow-up email after our product demo meeting, thanking them for their time and proposing concrete next steps for implementation",
            "tone": "formal",
            "description": "Post-meeting thank you and next steps",
            "icon": "📅"
        },
        "Thank You Note": {
            "prompt": "Write a genuine thank you email for their time, valuable feedback on our product, and insightful suggestions for improvement",
            "tone": "empathetic",
            "description": "Sincere gratitude expression",
            "icon": "🙏"
        },
        "Project Update": {
            "prompt": "Write a status update email about the Q4 project progress to stakeholders, highlighting achievements and addressing any concerns",
            "tone": "formal",
            "description": "Professional status update",
            "icon": "📊"
        },
        "Networking": {
            "prompt": "Write a LinkedIn connection follow-up email to continue the conversation we started at the tech conference about AI applications",
            "tone": "casual",
            "description": "Friendly professional networking",
            "icon": "🤝"
        },
        "Apology": {
            "prompt": "Write a sincere apology email for missing our scheduled meeting due to an emergency, taking full responsibility and proposing alternative times",
            "tone": "empathetic",
            "description": "Genuine apology and rescheduling",
            "icon": "🙇"
        }
    }
    
    col1, col2, col3 = st.columns(3)
    
    for idx, (template_name, template_data) in enumerate(templates.items()):
        col = [col1, col2, col3][idx % 3]
        
        with col:
            with st.container():
                st.markdown(f"### {template_data['icon']} {template_name}")
                st.caption(template_data["description"])
                st.code(template_data["prompt"][:100] + "...", language=None)
                
                if st.button(f"Use Template", key=f"template_{idx}"):
                    st.session_state['compose_prompt'] = template_data["prompt"]
                    st.success(f"✅ Template loaded! Switch to Compose tab")
                    st.rerun()

# TAB 3: History
with tab3:
    st.header("📚 Draft History")
    
    history = memory.get_draft_history(user_id, limit=20)
    
    if not history:
        st.info("📝 No draft history yet. Start composing emails to see them here!")
    else:
        st.markdown(f"Showing last {len(history)} drafts")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            all_intents = list(set(d.get('intent', 'unknown') for d in history))
            filter_intent = st.selectbox("Filter by Intent", ["All"] + all_intents)
        with col2:
            all_tones = list(set(d.get('tone', 'unknown') for d in history))
            filter_tone = st.selectbox("Filter by Tone", ["All"] + all_tones)
        with col3:
            sort_by = st.selectbox("Sort by", ["Recent", "Quality Score"])
        
        # Apply filters
        filtered_history = history
        if filter_intent != "All":
            filtered_history = [d for d in filtered_history if d.get('intent') == filter_intent]
        if filter_tone != "All":
            filtered_history = [d for d in filtered_history if d.get('tone') == filter_tone]
        
        # Sort
        if sort_by == "Quality Score":
            filtered_history = sorted(filtered_history, 
                                    key=lambda x: x.get('quality_score', 0), 
                                    reverse=True)
        
        # Display
        for idx, draft_entry in enumerate(filtered_history):
            with st.expander(
                f"📧 {draft_entry.get('intent', 'Email').replace('_', ' ').title()} • "
                f"{draft_entry['timestamp'][:10]} • "
                f"Score: {draft_entry.get('quality_score', 'N/A')}"
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Original Prompt:**")
                    st.text(draft_entry.get('prompt', 'N/A')[:200] + "...")
                    
                    st.markdown("**Generated Draft:**")
                    st.text_area(
                        "Draft",
                        value=draft_entry.get('draft', 'N/A'),
                        height=150,
                        key=f"history_{idx}",
                        disabled=True
                    )
                
                with col2:
                    st.metric("Tone", draft_entry.get('tone', 'N/A').title())
                    st.metric("Intent", draft_entry.get('intent', 'N/A').replace('_', ' ').title())
                    if draft_entry.get('quality_score'):
                        st.metric("Quality", f"{draft_entry.get('quality_score'):.2f}")
                    
                    if st.button("🔄 Regenerate", key=f"regen_{idx}"):
                        st.session_state['compose_prompt'] = draft_entry.get('prompt', '')
                        st.success("Prompt loaded! Go to Compose tab")
                        st.rerun()

# TAB 4: Analytics
with tab4:
    st.header("📊 Analytics Dashboard")
    
    metrics = monitor.get_metrics_summary()
    
    # Overview Cards
    st.markdown("### 📈 Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Requests",
            metrics["total_requests"],
            delta=f"+{metrics['today']['requests']} today"
        )
    with col2:
        st.metric("Success Rate", metrics["success_rate"])
    with col3:
        st.metric(
            "Total Cost",
            metrics["total_cost"],
            delta=f"+{metrics['today']['cost']} today"
        )
    with col4:
        st.metric("Avg Latency", metrics["avg_latency"])
    
    # Token usage
    st.markdown("### 🪙 Token Usage")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tokens", f"{metrics['total_tokens']:,}")
    with col2:
        st.metric("Input Tokens", f"{metrics['input_tokens']:,}")
    with col3:
        st.metric("Output Tokens", f"{metrics['output_tokens']:,}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Email Types Distribution")
        if metrics["by_intent"]:
            intent_data = pd.DataFrame(
                list(metrics["by_intent"].items()),
                columns=['Intent', 'Count']
            )
            fig = px.pie(intent_data, values='Count', names='Intent', 
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet")
    
    with col2:
        st.markdown("### 🎭 Tone Preferences")
        if metrics["by_tone"]:
            tone_data = pd.DataFrame(
                list(metrics["by_tone"].items()),
                columns=['Tone', 'Count']
            )
            fig = px.bar(tone_data, x='Tone', y='Count',
                        color='Tone',
                        color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet")
    
    # Quality scores over time
    if metrics.get("quality_scores"):
        st.markdown("### 📈 Quality Scores Over Time")
        quality_df = pd.DataFrame(metrics["quality_scores"])
        quality_df['timestamp'] = pd.to_datetime(quality_df['timestamp'])
        
        fig = px.line(quality_df, x='timestamp', y='score',
                     title='Email Quality Trend',
                     labels={'score': 'Quality Score', 'timestamp': 'Time'})
        fig.add_hline(y=0.8, line_dash="dash", line_color="green", 
                     annotation_text="Target: 0.8")
        st.plotly_chart(fig, use_container_width=True)
    
    # Error analysis
    if metrics["errors"]:
        st.markdown("### ⚠️ Error Analysis")
        error_data = pd.DataFrame(
            list(metrics["errors"].items()),
            columns=['Error Type', 'Count']
        )
        st.dataframe(error_data, use_container_width=True)
    
    # Export options
    st.markdown("### 📥 Export Data")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Export Metrics as JSON"):
            metrics_json = json.dumps(metrics, indent=2)
            st.download_button(
                "Download JSON",
                metrics_json,
                file_name=f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    with col2:
        if st.button("📋 Export History as CSV"):
            history = memory.get_draft_history(user_id, limit=100)
            if history:
                df = pd.DataFrame(history)
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    file_name=f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

# Footer
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("Built with ❤️ using LangChain & LangGraph")
with col2:
    st.markdown("Powered by Google Gemini 2.0 Flash")
with col3:
    st.markdown(f"Version 1.0.0 • {datetime.now().year}")
with col4:
    if st.button("📖 View Docs"):
        st.info("Documentation: See README.md")
```

---

## 🌟 Day 2: Advanced Features (6-8 hours)

### Hour 1-2: A/B Testing Engine

#### Create `src/agents/ab_testing.py`
```python
from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

class ABTestingEngine:
    """Generate multiple email variants for A/B testing"""
    
    def __init__(self, llm):
        self.llm = llm
        self.strategies = {
            "shorter": "Create a more concise version (30% shorter)",
            "more_personal": "Make it more personal and warm",
            "more_direct": "Make it more direct and action-oriented",
            "storytelling": "Add a brief story or example",
            "data_driven": "Add specific numbers or data points",
            "question_based": "Start with an engaging question"
        }
        
        self.variant_prompt = ChatPromptTemplate.from_template("""
        You are an expert at creating email variants for A/B testing.
        
        Original Email:
        {original_email}
        
        Strategy: {strategy}
        
        Create a variant of this email that applies the strategy while:
        1. Keeping the same core message and intent
        2. Maintaining the same tone
        3. Ensuring it's still professional and effective
        
        Return ONLY the variant email, no explanations.
        """)
    
    def generate_variants(self, 
                         original_draft: str, 
                         num_variants: int = 2,
                         strategies: List[str] = None) -> List[Dict]:
        """Generate email variants"""
        
        if strategies is None:
            # Use default strategies
            strategies = list(self.strategies.keys())[:num_variants]
        
        variants = [{"version": "Original", "draft": original_draft, "strategy": "baseline"}]
        
        for idx, strategy in enumerate(strategies[:num_variants]):
            try:
                chain = self.variant_prompt | self.llm
                response = chain.invoke({
                    "original_email": original_draft,
                    "strategy": self.strategies.get(strategy, strategy)
                })
                
                variant_draft = response.content.strip()
                
                # Calculate differences
                differences = self._analyze_differences(original_draft, variant_draft)
                
                variants.append({
                    "version": f"Variant {chr(65 + idx)}",  # A, B, C...
                    "strategy": strategy,
                    "draft": variant_draft,
                    "differences": differences
                })
                
            except Exception as e:
                print(f"Error generating variant {strategy}: {e}")
        
        return variants
    
    def _analyze_differences(self, original: str, variant: str) -> Dict:
        """Analyze key differences between versions"""
        return {
            "word_count_change": len(variant.split()) - len(original.split()),
            "char_count_change": len(variant) - len(original),
            "tone_shift": self._detect_tone_shift(original, variant)
        }
    
    def _detect_tone_shift(self, original: str, variant: str) -> str:
        """Simple tone shift detection"""
        # Check for formal vs casual indicators
        formal_words = ["regard", "sincerely", "please", "thank you"]
        casual_words = ["hey", "hi", "thanks", "cheers"]
        
        orig_formal = sum(1 for w in formal_words if w in original.lower())
        var_formal = sum(1 for w in formal_words if w in variant.lower())
        
        if var_formal > orig_formal:
            return "More formal"
        elif var_formal < orig_formal:
            return "More casual"
        return "Similar"
    
    def compare_variants(self, variants: List[Dict]) -> Dict:
        """Compare variants and provide recommendations"""
        
        comparison = {
            "total_variants": len(variants),
            "recommendations": []
        }
        
        # Find shortest and longest
        shortest = min(variants, key=lambda v: len(v["draft"].split()))
        longest = max(variants, key=lambda v: len(v["draft"].split()))
        
        comparison["shortest"] = shortest["version"]
        comparison["longest"] = longest["version"]
        
        # Recommendations
        if len(shortest["draft"].split()) < 100:
            comparison["recommendations"].append(
                f"{shortest['version']}: Good for busy executives"
            )
        
        if len(longest["draft"].split()) > 200:
            comparison["recommendations"].append(
                f"{longest['version']}: Best for detailed proposals"
            )
        
        return comparison
```

### Hour 2-3: Template Engine with Variables

#### Create `src/utils/template_engine.py`
```python
from string import Template
from typing import Dict, List
import json
import os

class TemplateEngine:
    """Advanced template system with variable substitution"""
    
    def __init__(self, templates_dir: str = "data/templates"):
        self.templates_dir = templates_dir
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load templates from JSON files"""
        templates = {}
        
        # Built-in templates
        templates["sales_outreach"] = {
            "name": "Sales Outreach",
            "template": Template("""Dear $recipient_name,

I noticed that $company_name is $pain_point. I believe our $product_name could help you $value_proposition.

Key benefits:
$benefits

Would you be open to a brief call next week to discuss how we can help?

$cta

Best regards,
$sender_name
$sender_title"""),
            "variables": [
                "recipient_name", "company_name", "pain_point", 
                "product_name", "value_proposition", "benefits", 
                "cta", "sender_name", "sender_title"
            ],
            "example": {
                "recipient_name": "Jane Smith",
                "company_name": "TechCorp",
                "pain_point": "scaling your customer support operations",
                "product_name": "AI Support Assistant",
                "value_proposition": "reduce response times by 60%",
                "benefits": "- 24/7 automated responses\n- Seamless human handoff\n- Multi-language support",
                "cta": "I have some time available Tuesday or Thursday afternoon.",
                "sender_name": "John Doe",
                "sender_title": "Sales Director"
            }
        }
        
        templates["meeting_request"] = {
            "name": "Meeting Request",
            "template": Template("""Hi $recipient_name,

I hope this email finds you well.

I wanted to reach out regarding $meeting_purpose. I believe a brief conversation would be valuable for both of us.

Proposed Topics:
$agenda_items

The meeting should take approximately $duration.

$scheduling_options

Looking forward to connecting!

Best,
$sender_name"""),
            "variables": [
                "recipient_name", "meeting_purpose", "agenda_items",
                "duration", "scheduling_options", "sender_name"
            ],
            "example": {
                "recipient_name": "Alex",
                "meeting_purpose": "exploring partnership opportunities",
                "agenda_items": "- Overview of our platform\n- Integration possibilities\n- Timeline discussion",
                "duration": "30 minutes",
                "scheduling_options": "Would any of these times work for you?\n- Tuesday, 2pm EST\n- Wednesday, 10am EST\n- Thursday, 3pm EST",
                "sender_name": "Sarah"
            }
        }
        
        # Load from files
        if os.path.exists(self.templates_dir):
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.templates_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            template_data = json.load(f)
                            template_id = filename.replace('.json', '')
                            templates[template_id] = template_data
                    except Exception as e:
                        print(f"Error loading template {filename}: {e}")
        
        return templates
    
    def get_template(self, template_id: str) -> Dict:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[Dict]:
        """List all available templates"""
        return [
            {
                "id": tid,
                "name": t.get("name", tid),
                "variables": t.get("variables", [])
            }
            for tid, t in self.templates.items()
        ]
    
    def fill_template(self, template_id: str, variables: Dict) -> str:
        """Fill template with variables"""
        template_data = self.templates.get(template_id)
        if not template_data:
            raise ValueError(f"Template '{template_id}' not found")
        
        template = template_data.get("template")
        if isinstance(template, str):
            template = Template(template)
        
        try:
            return template.safe_substitute(variables)
        except Exception as e:
            raise ValueError(f"Error filling template: {e}")
    
    def get_example(self, template_id: str) -> Dict:
        """Get example variables for template"""
        template_data = self.templates.get(template_id)
        if template_data:
            return template_data.get("example", {})
        return {}
    
    def validate_variables(self, template_id: str, variables: Dict) -> Dict:
        """Validate that all required variables are provided"""
        template_data = self.templates.get(template_id)
        if not template_data:
            return {"valid": False, "error": "Template not found"}
        
        required_vars = template_data.get("variables", [])
        missing = [v for v in required_vars if v not in variables]
        
        if missing:
            return {
                "valid": False,
                "missing_variables": missing
            }
        
        return {"valid": True}
```

### Hour 3-4: Enhanced Memory Manager

#### Update `src/memory/memory_manager.py`
```python
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class MemoryManager:
    """Enhanced memory management with analytics"""
    
    def __init__(self, 
                 profiles_path: str = "src/memory/user_profiles.json",
                 history_path: str = "src/memory/draft_history.json"):
        self.profiles_path = profiles_path
        self.history_path = history_path
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Create memory files if they don't exist"""
        for path in [self.profiles_path, self.history_path]:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    json.dump({}, f)
    
    # Profile Management
    def get_profile(self, user_id: str = "default") -> Dict:
        """Get user profile"""
        with open(self.profiles_path, 'r') as f:
            profiles = json.load(f)
        return profiles.get(user_id, self._default_profile())
    
    def save_profile(self, user_id: str, profile_data: Dict):
        """Save user profile"""
        with open(self.profiles_path, 'r') as f:
            profiles = json.load(f)
        
        profiles[user_id] = profile_data
        
        with open(self.profiles_path, 'w') as f:
            json.dump(profiles, f, indent=2)
    
    def _default_profile(self) -> Dict:
        """Default profile template"""
        return {
            "user_name": "User",
            "user_title": "",
            "user_company": "",
            "signature": "\n\nBest regards",
            "style_notes": "professional and clear",
            "preferences": {
                "default_tone": "formal",
                "preferred_length": 150
            },
            "created_at": datetime.now().isoformat(),
            "stats": {
                "total_emails": 0,
                "favorite_tone": "formal",
                "avg_quality_score": 0.0
            }
        }
    
    # Draft History
    def save_draft(self, user_id: str, draft_data: Dict):
        """Save draft to history"""
        with open(self.history_path, 'r') as f:
            history = json.load(f)
        
        if user_id not in history:
            history[user_id] = []
        
        draft_entry = {
            "draft_id": f"draft_{len(history[user_id]) + 1}",
            "timestamp": datetime.now().isoformat(),
            **draft_data
        }
        
        history[user_id].append(draft_entry)
        
        # Keep only last 100 drafts
        history[user_id] = history[user_id][-100:]
        
        with open(self.history_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        # Update profile stats
        self._update_profile_stats(user_id, draft_data)
    
    def get_draft_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent draft history"""
        with open(self.history_path, 'r') as f:
            history = json.load(f)
        
        user_history = history.get(user_id, [])
        return user_history[-limit:][::-1]  # Most recent first
    
    def _update_profile_stats(self, user_id: str, draft_data: Dict):
        """Update user profile statistics"""
        profile = self.get_profile(user_id)
        
        stats = profile.get("stats", {
            "total_emails": 0,
            "favorite_tone": "formal",
            "avg_quality_score": 0.0
        })
        
        # Update counters
        stats["total_emails"] += 1
        
        # Update quality score average
        quality_score = draft_data.get("quality_score", 0.7)
        current_avg = stats.get("avg_quality_score", 0.0)
        total = stats["total_emails"]
        stats["avg_quality_score"] = ((current_avg * (total - 1)) + quality_score) / total
        
        # Update favorite tone
        tone = draft_data.get("tone", "formal")
        # Track tone usage (simplified)
        stats["favorite_tone"] = tone
        
        profile["stats"] = stats
        self.save_profile(user_id, profile)
    
    def learn_from_edits(self, user_id: str, original: str, edited: str):
        """Learn from user edits to improve personalization"""
        analysis = self._analyze_edits(original, edited)
        
        if analysis:
            profile = self.get_profile(user_id)
            profile.setdefault("learned_preferences", {})
            profile["learned_preferences"].update(analysis)
            self.save_profile(user_id, profile)
    
    def _analyze_edits(self, original: str, edited: str) -> Dict:
        """Analyze what changed in the edit"""
        analysis = {}
        
        # Check tone changes
        casual_indicators = ["hey", "hi", "thanks", "cheers"]
        formal_indicators = ["dear", "sincerely", "regards"]
        
        orig_casual = sum(1 for ind in casual_indicators if ind in original.lower())
        edit_casual = sum(1 for ind in casual_indicators if ind in edited.lower())
        
        if edit_casual > orig_casual:
            analysis["tone_preference"] = "casual"
        elif edit_casual < orig_casual:
            analysis["tone_preference"] = "formal"
        
        # Length preference
        orig_len = len(original.split())
        edit_len = len(edited.split())
        
        if abs(edit_len - orig_len) > 20:
            analysis["preferred_length"] = edit_len
        
        return analysis
    
    def get_user_analytics(self, user_id: str) -> Dict:
        """Get user analytics"""
        profile = self.get_profile(user_id)
        history = self.get_draft_history(user_id, limit=100)
        
        # Calculate stats
        if history:
            intents = [d.get('intent', 'unknown') for d in history]
            tones = [d.get('tone', 'unknown') for d in history]
            quality_scores = [d.get('quality_score', 0) for d in history if d.get('quality_score')]
            
            # Recent activity (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent = [d for d in history 
                     if datetime.fromisoformat(d['timestamp']) > week_ago]
            
            return {
                "total_emails": len(history),
                "this_week": len(recent),
                "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                "most_used_intent": max(set(intents), key=intents.count) if intents else "N/A",
                "most_used_tone": max(set(tones), key=tones.count) if tones else "N/A",
                "profile_stats": profile.get("stats", {})
            }
        
        return {
            "total_emails": 0,
            "this_week": 0,
            "avg_quality_score": 0,
            "most_used_intent": "N/A",
            "most_used_tone": "N/A"
        }
```

---

## 🚀 Day 3: Final Polish & Testing (6-8 hours)

### Hour 1-2: Comprehensive Testing

#### Create `tests/test_monitoring.py`
```python
import pytest
from src.utils.monitoring import MonitoringManager
from src.utils.token_counter import TokenCounter
from src.utils.rate_limiter import RateLimiter
import time

class TestMonitoring:
    def test_monitor_track_request(self):
        monitor = MonitoringManager()
        initial_count = monitor.metrics["total_requests"]
        
        monitor.track_request(
            intent="outreach",
            tone="formal",
            success=True,
            latency=1.5,
            input_tokens=100,
            output_tokens=200,
            cost=0.0001
        )
        
        assert monitor.metrics["total_requests"] == initial_count + 1
        assert monitor.metrics["successful_requests"] > 0
    
    def test_monitor_metrics_summary(self):
        monitor = MonitoringManager()
        summary = monitor.get_metrics_summary()
        
        assert "total_requests" in summary
        assert "success_rate" in summary
        assert "total_cost" in summary

class TestTokenCounter:
    def test_count_tokens(self):
        counter = TokenCounter()
        text = "This is a test email."
        tokens = counter.count_tokens(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_estimate_cost(self):
        counter = TokenCounter()
        cost = counter.estimate_cost(1000, 500)
        
        assert cost > 0
        assert isinstance(cost, float)
    
    def test_token_breakdown(self):
        counter = TokenCounter()
        breakdown = counter.get_token_breakdown(
            "Input text here",
            "Output text here"
        )
        
        assert "input_tokens" in breakdown
        assert "output_tokens" in breakdown
        assert "total_tokens" in breakdown
        assert "estimated_cost" in breakdown

class TestRateLimiter:
    def test_can_make_request(self):
        limiter = RateLimiter(max_requests_per_minute=10)
        can_proceed, msg = limiter.can_make_request()
        
        assert can_proceed == True
        assert msg is None
    
    def test_rate_limit_exceeded(self):
        limiter = RateLimiter(max_requests_per_minute=2)
        
        # Make requests up to limit
        limiter.record_request()
        limiter.record_request()
        
        # Should be blocked
        can_proceed, msg = limiter.can_make_request()
        assert can_proceed == False
        assert "Rate limit exceeded" in msg
    
    def test_cost_limit(self):
        limiter = RateLimiter(daily_cost_limit=0.01)
        
        # Record expensive request
        limiter.record_request(cost=0.02)
        
        # Should be blocked
        can_proceed, msg = limiter.can_make_request()
        assert can_proceed == False
        assert "cost limit" in msg.lower()
```

#### Create `tests/test_integration.py`
```python
import pytest
from src.workflow.langgraph_flow import generate_email
import time

class TestIntegration:
    def test_full_workflow(self):
        """Test complete email generation workflow"""
        result = generate_email(
            user_input="Write a thank you email to Sarah for the meeting",
            tone="formal",
            user_id="test_user"
        )
        
        assert "final_draft" in result or "draft" in result
        assert result.get("intent") is not None
        assert result.get("monitoring") is not None
    
    def test_different_tones(self):
        """Test workflow with different tones"""
        tones = ["formal", "casual", "assertive", "empathetic"]
        
        for tone in tones:
            result = generate_email(
                user_input="Write a follow-up email",
                tone=tone,
                user_id="test_user"
            )
            
            assert result is not None
            time.sleep(1)  # Rate limit consideration
    
    def test_error_handling(self):
        """Test error handling in workflow"""
        result = generate_email(
            user_input="",  # Empty input
            tone="formal"
        )
        
        # Should handle gracefully
        assert result is not None
```

### Hour 2-3: Create README and Documentation

#### Create `README.md`
```markdown
# AI Email Assistant Pro 🚀
### Production-Ready Email Generation with Full Observability

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-latest-green.svg)](https://python.langchain.com/)

A sophisticated multi-agent email assistant built with LangChain, LangGraph, and Google Gemini, featuring comprehensive monitoring, quality scoring, and A/B testing capabilities.

## ✨ Features

### Core Capabilities
- 🤖 **7 Specialized Agents**: Input Parser, Intent Detector, Draft Writer, Tone Stylist, Personalization, Review, Router
- 🎭 **Multi-Tone Support**: Formal, Casual, Assertive, Empathetic
- 📊 **Quality Scoring**: Comprehensive email quality analysis with actionable recommendations
- 🔄 **A/B
