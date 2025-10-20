# User Preferences Feature - Implementation Guide

## 🎯 Overview

This document describes the implementation of the **User Preferences System** for the Math AI Agent. The system captures user preferences **before** the agentic flow starts and feeds them through all cognitive layers (Perception → Memory → Decision → Action).

---

## 🚀 What Was Implemented

### 1. **Chrome Extension UI Enhancement** (`chrome-extension/popup.html`)

Added a user-friendly dropdown for selecting mathematical ability preference:

```html
<div class="preference-section">
  <label for="math-ability">Your Math Preference:</label>
  <select id="math-ability">
    <option value="logical">Logical (Proofs & Reasoning)</option>
    <option value="arithmetic" selected>Arithmetic (Basic Calculations)</option>
    <option value="algebra">Algebra (Equations & Symbols)</option>
    <option value="geometry">Geometry (Shapes & Spaces)</option>
    <option value="statistics">Statistics (Data & Analysis)</option>
  </select>
</div>
```

**Visual Features:**
- Styled preference section with light blue background
- Positioned above the query input
- Default selection: "Arithmetic"

---

### 2. **Frontend JavaScript Updates** (`chrome-extension/popup.js`)

**Changes:**
- Captures preference value from dropdown
- Sends preferences along with query to server

```javascript
const mathAbility = mathAbilitySelect.value;

body: JSON.stringify({ 
  query: query,
  preferences: {
    math_ability: mathAbility
  }
})
```

---

### 3. **Backend Server Updates** (`server.py`)

**Changes:**
- Accepts `preferences` parameter in `/api/query` endpoint
- Logs user preferences for debugging
- Passes preferences to AI agent

```python
preferences = data.get('preferences', {})
logger.info(f"User preferences: {preferences}")
result = await ai_main(query, preferences=preferences)
```

---

### 4. **Agent Orchestrator Updates** (`agent/ai_agent.py`)

**Changes:**
- `main()` function accepts `preferences` parameter
- `CognitiveAgent` class stores preferences
- Preferences are passed to Perception and Decision layers during initialization
- New method `_store_preferences()` persists preferences in Memory Layer

```python
async def main(query: str, preferences: Optional[Dict[str, Any]] = None):
    agent = CognitiveAgent(session, tools, preferences=preferences)
    ...

class CognitiveAgent:
    def __init__(self, session, tools, preferences=None):
        self.preferences = preferences or {}
        self.perception = PerceptionLayer(model, user_preferences=self.preferences)
        self.decision = DecisionLayer(model, user_preferences=self.preferences)
        
        if self.preferences:
            self._store_preferences()
```

---

### 5. **Perception Layer Updates** (`agent/perception.py`)

**Changes:**
- Constructor accepts `user_preferences` parameter
- Formats preferences into prompt context
- LLM receives preference information for better understanding

```python
class PerceptionLayer:
    def __init__(self, model, user_preferences=None):
        self.user_preferences = user_preferences or {}
    
    async def perceive(self, query):
        prefs_text = "\n".join([f"- {k}: {v}" for k, v in self.user_preferences.items()])
        prompt = PERCEPTION_PROMPT.format(
            user_preferences=prefs_text,
            query=query
        )
```

---

### 6. **Decision Layer Updates** (`agent/decision.py`)

**Changes:**
- Constructor accepts `user_preferences` parameter
- Includes preferences in decision-making prompt
- AI can tailor action plans based on user preferences

```python
class DecisionLayer:
    def __init__(self, model, user_preferences=None):
        self.user_preferences = user_preferences or {}
    
    async def decide(self, ...):
        prefs_text = "\n".join([f"- {k}: {v}" for k, v in self.user_preferences.items()])
        prompt = DECISION_PROMPT.format(
            user_preferences=prefs_text,
            ...
        )
```

---

### 7. **Memory Layer Integration** (`agent/ai_agent.py`)

**Preference Storage:**
- Preferences are stored as facts in memory
- Added to `user_preferences` dictionary in Memory State
- Persisted to disk for future sessions

```python
def _store_preferences(self):
    for key, value in self.preferences.items():
        preference_text = f"User preference: {key} = {value}"
        self.memory.store_fact(
            content=preference_text,
            source="user_preferences",
            relevance_score=1.0
        )
    self.memory.save_memory()
```

---

### 8. **Prompt Updates** (`agent/prompts.py`)

**Changes:**
- Added `{user_preferences}` placeholder to `PERCEPTION_PROMPT`
- Added `{user_preferences}` placeholder to `DECISION_PROMPT`
- LLM now has context about user preferences throughout cognitive flow

---

## 📋 How It Works (Flow Diagram)

```
1. User opens Chrome Extension
   ↓
2. User selects "math_ability" from dropdown (e.g., "arithmetic")
   ↓
3. User enters query (e.g., "add 100 and 200")
   ↓
4. Frontend captures:
   - query: "add 100 and 200"
   - preferences: { math_ability: "arithmetic" }
   ↓
5. POST to /api/query with both query and preferences
   ↓
6. Server passes preferences to agent
   ↓
7. Agent stores preferences in Memory Layer
   ↓
8. Agent initializes layers with preferences
   ↓
9. Perception Layer receives:
   **User Preferences:**
   - math_ability: arithmetic
   
   Query: "add 100 and 200"
   ↓
10. Decision Layer receives preferences in context
    ↓
11. Agent executes with preference-aware understanding
    ↓
12. Result returned to user
```

---

## 🧪 Testing Instructions

### Test Case 1: Basic Arithmetic Query

1. **Start the server:**
   ```bash
   uv run .\server.py
   ```

2. **Open Chrome Extension**

3. **Select Preference:**
   - Dropdown: Select "Arithmetic (Basic Calculations)"

4. **Enter Query:**
   ```
   add 50 and 30
   ```

5. **Expected Behavior:**
   - Server logs show: `User preferences: {'math_ability': 'arithmetic'}`
   - Agent logs show: `[AGENT] User preferences loaded: {'math_ability': 'arithmetic'}`
   - Memory file contains: `"User preference: math_ability = arithmetic"`
   - Result: `80`

---

### Test Case 2: Algebra Preference

1. **Select Preference:**
   - Dropdown: Select "Algebra (Equations & Symbols)"

2. **Enter Query:**
   ```
   solve for x: 2x + 5 = 15
   ```

3. **Expected Behavior:**
   - Agent understands algebraic context
   - Preferences logged and stored
   - Appropriate response based on algebra preference

---

### Test Case 3: Verify Persistence

1. **First Query with preference "arithmetic"**
   - Execute query: "add 10 and 20"

2. **Check Memory File:**
   ```bash
   cat logs/agent_memory.json
   ```

3. **Verify:**
   - File contains preference facts
   - `user_preferences` dictionary has `math_ability` entry

---

## 📁 Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `chrome-extension/popup.html` | Added preference dropdown | UI for preference selection |
| `chrome-extension/popup.js` | Capture & send preferences | Frontend logic |
| `server.py` | Accept preferences parameter | Backend API |
| `agent/ai_agent.py` | Store & distribute preferences | Orchestration |
| `agent/perception.py` | Use preferences in prompts | Context-aware perception |
| `agent/decision.py` | Use preferences in planning | Context-aware decisions |
| `agent/prompts.py` | Add preference placeholders | LLM context |

---

## 🎨 Extensibility

### Adding More Preferences

Want to add more preferences? Here's how:

1. **Add to UI (`popup.html`):**
   ```html
   <select id="location">
     <option value="us">United States</option>
     <option value="uk">United Kingdom</option>
   </select>
   ```

2. **Capture in JS (`popup.js`):**
   ```javascript
   const location = document.getElementById('location').value;
   
   preferences: {
     math_ability: mathAbility,
     location: location
   }
   ```

3. **That's it!** The rest of the system automatically:
   - Accepts the new preference
   - Stores it in memory
   - Includes it in prompts
   - Makes it available to all layers

---

## 🔍 Debugging

### Check Preferences in Logs

1. **Server logs:**
   ```
   2025-10-19 20:40:25,646 - INFO - User preferences: {'math_ability': 'arithmetic'}
   ```

2. **Agent logs:**
   ```
   2025-10-19 20:40:26,355 - INFO - [AGENT] User preferences loaded: {'math_ability': 'arithmetic'}
   2025-10-19 20:40:26,356 - INFO - [AGENT] Stored 1 user preferences in memory
   ```

3. **Memory file:**
   ```bash
   cat logs/agent_memory.json | grep "math_ability"
   ```

---

## 💡 Key Benefits

1. **🎯 Personalization**: Agent adapts responses based on user preferences
2. **🧠 Context Awareness**: All cognitive layers have access to preferences
3. **💾 Persistence**: Preferences are stored and can be retrieved across sessions
4. **📊 Logging**: Full traceability of preference usage
5. **🔄 Extensibility**: Easy to add more preference types
6. **🏗️ Clean Architecture**: Preferences flow naturally through cognitive layers

---

## ✅ Success Criteria

- [x] Chrome extension has preference dropdown
- [x] Preferences are sent with every query
- [x] Server accepts and logs preferences
- [x] Agent stores preferences in Memory Layer
- [x] Perception Layer receives preferences in prompt
- [x] Decision Layer receives preferences in prompt
- [x] Preferences persist in `agent_memory.json`
- [x] All layers initialized with preference context

---

## 🚀 Next Steps

1. **Test the implementation** with different preferences
2. **Verify memory persistence** across sessions
3. **Observe LLM behavior** with different preference values
4. **Add more preferences** if needed (location, language, etc.)
5. **Monitor logs** to ensure preferences flow correctly

---

## 📝 Notes

- Preferences are optional - system works without them
- Default behavior maintained if no preferences provided
- Preferences stored with `relevance_score=1.0` for high priority
- Memory file includes both facts and structured user_preferences dict

---

**Implementation Status:** ✅ **Complete**

**Tested:** Ready for user testing

**Documentation:** Complete

