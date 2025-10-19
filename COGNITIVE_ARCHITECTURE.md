# Cognitive Architecture Implementation

## 🧠 Overview

The AI Agent has been successfully refactored from a single "Augmented LLM" approach to a **structured 4-layer cognitive architecture** inspired by human cognition.

---

## 🏗️ Architecture

### Before: Augmented LLM (Monolithic)
```
User Query → Single LLM Loop → Response
   ↓
[One big prompt handles everything]
```

### After: Cognitive Layers (Modular)
```
User Query
   ↓
👁️ PERCEIVE: Extract intent, entities, facts
   ↓
🧠 REMEMBER: Store observations, retrieve context
   ↓
🧭 DECIDE: Plan actions based on perception + memory
   ↓
🎯 ACT: Execute tools and generate responses
   ↓
Response (with memory persistence)
```

---

## 📁 New File Structure

```
agent/
├── __init__.py              # Updated exports
├── models.py                # ✨ NEW: Cognitive layer Pydantic models
├── prompts.py               # ✨ NEW: PERCEPTION_PROMPT, DECISION_PROMPT
├── ai_agent.py              # ♻️ REFACTORED: Orchestrator for 4 layers
│
├── perception.py            # 🆕 LAYER 1: Understanding input
├── memory.py                # 🆕 LAYER 2: Storing & retrieving facts
├── decision.py              # 🆕 LAYER 3: Planning actions
└── action.py                # 🆕 LAYER 4: Executing tools
```

---

## 🔍 Layer Details

### 1. 👁️ Perception Layer (`perception.py`)

**Purpose:** Translate raw user input → structured information

**Key Features:**
- Uses LLM to extract intent, entities, and facts
- Identifies thought type (Planning, Analysis, Decision Making, etc.)
- Determines if tools are required
- Returns validated `PerceptionOutput` (Pydantic model)

**Example:**
```python
Input: "Add 2 and 3 and show in PowerPoint"

Output: PerceptionOutput(
    intent="multi_step",
    entities={"numbers": [2, 3], "operation": "addition", "output": "PowerPoint"},
    thought_type="Planning",
    extracted_facts=[
        "User wants to add 2 and 3",
        "Result should be displayed in PowerPoint",
        "Requires math calculation followed by PowerPoint operation"
    ],
    requires_tools=True,
    confidence=1.0
)
```

---

### 2. 🧠 Memory Layer (`memory.py`)

**Purpose:** Store facts and context for future reasoning

**Key Differences from Old System:**
- **Old:** Stored function call history
- **New:** Stores semantic facts like a human brain

**Features:**
- Store individual facts with timestamps and relevance scores
- Retrieve relevant facts based on queries (simple keyword matching for now)
- Update user preferences and context
- Persist memory to JSON file (`logs/agent_memory.json`)
- Will be upgraded to vector database in Session 7

**Example:**
```python
# Store facts
memory.store_fact("User wants to add 2 and 3")
memory.store_fact("Result should be displayed in PowerPoint")

# Retrieve relevant facts
query = MemoryQuery(query="PowerPoint presentation", max_results=5)
results = memory.retrieve_relevant_facts(query)
# Returns facts about PowerPoint operations
```

---

### 3. 🧭 Decision Layer (`decision.py`)

**Purpose:** Create action plans based on perception and memory

**Key Features:**
- Uses LLM to reason about what actions to take
- Considers:
  - Current perception (intent, entities, facts)
  - Retrieved memory (relevant facts, context)
  - Available tools
- Returns `DecisionOutput` with step-by-step action plan
- Each step has reasoning, parameters, and type

**Example:**
```python
Input:
- Perception: "User wants to add 2 and 3"
- Memory: [previous math operations]
- Available Tools: [t_number_list_to_sum, open_powerpoint, ...]

Output: DecisionOutput(
    action_plan=[
        ActionStep(
            step_number=1,
            action_type="tool_call",
            description="Add numbers 2 and 3",
            tool_name="t_number_list_to_sum",
            parameters={"numbers": [2, 3]},
            reasoning="User wants simple addition"
        ),
        ActionStep(
            step_number=2,
            action_type="response",
            description="Return result to user",
            reasoning="Calculation complete"
        )
    ],
    reasoning="Simple arithmetic query",
    confidence=1.0,
    should_continue=False
)
```

---

### 4. 🎯 Action Layer (`action.py`)

**Purpose:** Execute the action plan

**Features:**
- Executes tool calls via MCP
- Generates text responses
- Tracks execution time
- Returns facts to remember
- Handles errors gracefully

**Action Types:**
- `tool_call`: Execute MCP tools (math, PowerPoint, email, etc.)
- `response`: Generate text response
- `query_memory`: Query memory (placeholder for future)

**Example:**
```python
action_step = ActionStep(
    step_number=1,
    action_type="tool_call",
    tool_name="t_number_list_to_sum",
    parameters={"numbers": [2, 3]}
)

result = await action.execute(action_step)
# ActionResult(success=True, result=5, facts_to_remember=[...])
```

---

## 🔄 Execution Flow

```python
async def process_query(query: str):
    # ITERATION LOOP (max 5 iterations)
    while iteration < MAX_ITERATIONS:
        
        # 1. 👁️ PERCEIVE (first iteration only)
        if not perception:
            perception = await perception_layer.perceive(query)
            memory.store_facts(perception.extracted_facts)
        
        # 2. 🧠 REMEMBER
        memory_result = memory.retrieve_relevant_facts(query)
        
        # 3. 🧭 DECIDE
        decision = await decision_layer.decide(
            perception=perception,
            memory=memory_result,
            available_tools=tools
        )
        
        # 4. 🎯 ACT
        for action_step in decision.action_plan:
            result = await action_layer.execute(action_step)
            memory.store_facts(result.facts_to_remember)
        
        # Check if complete
        if not decision.should_continue:
            break
    
    # Save memory to disk
    memory.save_memory()
    
    return response
```

---

## 📊 New Pydantic Models

### Cognitive Layer Models (`agent/models.py`)

**Perception Models:**
- `PerceptionOutput`: Intent, entities, thought type, facts
- `ThoughtType`: Enum for cognitive thought categories

**Memory Models:**
- `MemoryFact`: Single fact with timestamp and relevance
- `MemoryState`: Complete memory (facts, preferences, context)
- `MemoryQuery`: Query for retrieving memories
- `MemoryRetrievalResult`: Retrieved facts and context

**Decision Models:**
- `ActionStep`: Single step in action plan
- `DecisionOutput`: Complete action plan with reasoning

**Action Models:**
- `ActionInput`: Input for action execution
- `ActionResult`: Result with success, error, facts

**Orchestration Models:**
- `CognitiveState`: Complete state of all 4 layers

---

## 🎯 Key Benefits

### 1. **Separation of Concerns**
Each layer has a clear, single responsibility:
- Perception: Understand
- Memory: Remember
- Decision: Plan
- Action: Execute

### 2. **Type Safety**
All data flow is validated with Pydantic models:
- No more "messy or malformed" data
- Automatic validation
- Better debugging

### 3. **Traceability**
Every layer logs its operations:
- What was perceived
- What was remembered
- Why decisions were made
- What actions were taken

### 4. **Maintainability**
Changes to one layer don't affect others:
- Want better memory? Update `memory.py`
- Want smarter decisions? Update `decision.py`
- Each layer can be tested independently

### 5. **Extensibility**
Easy to add new features:
- Vector database memory (Session 7)
- Chain-of-Thought reasoning (Session 5)
- Multi-agent collaboration
- External API integrations

---

## 🔧 Usage

### Run the Agent

```bash
# Via command line
python agent/ai_agent.py

# Via Flask server (existing integration)
python server.py
```

### Programmatic Usage

```python
from agent import CognitiveAgent, main

# Use the main function
response_json = await main("What is 2 + 3?")

# Or use the agent directly
agent = CognitiveAgent(session, tools)
response = await agent.process_query("Add 2 and 3")
```

---

## 📝 Memory Persistence

Memory is automatically saved to `logs/agent_memory.json`:

```json
{
  "facts": [
    {
      "content": "User wants to add 2 and 3",
      "timestamp": "2024-01-15T10:30:00",
      "source": "perception",
      "relevance_score": 1.0
    }
  ],
  "user_preferences": {},
  "context": {},
  "conversation_summary": ""
}
```

---

## 🚀 Future Enhancements

### Session 5: Chain-of-Thought
- Add explicit reasoning steps in decision layer
- Self-reflection mechanisms

### Session 7: Vector Database
- Replace keyword-based memory with semantic search
- Store embeddings for better retrieval

### Beyond
- Multi-agent collaboration
- Long-term memory with summarization
- Conditional logic and workflows
- External API integrations

---

## 📚 Examples

### Example 1: Simple Math

**Query:** "What is 2 + 3?"

**Flow:**
1. 👁️ Perceive: Intent=calculation, entities={numbers: [2,3]}
2. 🧠 Remember: Store fact "User wants to add 2 and 3"
3. 🧭 Decide: Plan = [call t_number_list_to_sum, respond]
4. 🎯 Act: Execute sum(2,3) → 5, respond with "5"

**Result:** `5`

---

### Example 2: Multi-step with PowerPoint

**Query:** "Add 2 and 3 and show in PowerPoint"

**Flow:**
1. 👁️ Perceive: Intent=multi_step, thought=Planning
2. 🧠 Remember: Store facts about calculation + PowerPoint
3. 🧭 Decide: Plan = [sum, open_ppt, draw_rectangle, add_text, close_ppt, respond]
4. 🎯 Act: Execute all 6 steps sequentially

**Result:** `5` (displayed in PowerPoint)

---

## ✅ Completed Refactoring

- [x] Create Pydantic models for all 4 layers
- [x] Implement Perception Layer (`perception.py`)
- [x] Implement Memory Layer (`memory.py`)
- [x] Implement Decision Layer (`decision.py`)
- [x] Implement Action Layer (`action.py`)
- [x] Add PERCEPTION_PROMPT and DECISION_PROMPT
- [x] Refactor `ai_agent.py` as orchestrator
- [x] Update exports in `__init__.py`
- [x] Fix linting errors

---

## 🎓 Theory to Implementation Mapping

| Theory Concept | Implementation |
|---------------|----------------|
| **Pydantic as backbone** | All layer I/O uses Pydantic models |
| **Perceive → Remember → Decide → Act** | 4 separate modules with clear data flow |
| **Memory stores facts, not history** | `MemoryFact` models with semantic content |
| **Agent = Brain with layers** | `CognitiveAgent` orchestrates all layers |
| **No more "augmented LLM"** | LLM used strategically in specific layers |

---

## 🎉 Success!

The agent now operates as a **structured, layered cognitive system** rather than a monolithic "call LLM and wait" approach. This architecture mirrors human cognition and provides a solid foundation for advanced AI capabilities.

**Welcome to the future of Agentic AI! 🚀**

