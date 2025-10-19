# Quick Start: Cognitive Architecture

## 🚀 Running the New Agent

### Method 1: Command Line (Direct)
```bash
python agent/ai_agent.py
```
Enter your query when prompted.

### Method 2: Flask Server (Chrome Extension)
```bash
# Terminal 1: Start MCP Server
python server_mcp/mcp_server.py dev

# Terminal 2: Start Flask Server
python server.py
```
Use Chrome extension as before.

---

## 🧪 Testing the New Architecture

### Test 1: Simple Math (Perception + Decision + Action)
```
Query: What is 2 + 3?

Expected Flow:
👁️ Perceive: Intent=calculation
🧠 Remember: Store "User wants to add 2 and 3"
🧭 Decide: Plan tool_call(t_number_list_to_sum)
🎯 Act: Execute sum → Result: 5
```

### Test 2: Multi-step (All Layers)
```
Query: Add 2 and 3 and show in PowerPoint

Expected Flow:
👁️ Perceive: Intent=multi_step, thought=Planning
🧠 Remember: Store math + PowerPoint facts
🧭 Decide: Plan 6 steps (sum, open, draw, text, close, respond)
🎯 Act: Execute all steps
```

### Test 3: Complex Query (Memory Integration)
```
Query 1: Calculate 10 + 20
Query 2: Multiply the previous result by 2

Expected:
- Query 1: Result = 30, stored in memory
- Query 2: Retrieves "previous result = 30" from memory, calculates 30 * 2 = 60
```

---

## 📊 Monitoring

### Logs
All cognitive operations are logged to:
```
logs/cognitive_agent_YYYYMMDD_HHMMSS.log
```

Look for:
- `👁️ PERCEIVING:` - Perception layer
- `🧠 Memory Layer` - Memory operations
- `🧭 DECIDING:` - Decision-making
- `🎯 EXECUTING:` - Action execution

### Memory File
Persistent memory is saved to:
```
logs/agent_memory.json
```

View this file to see what the agent remembers across sessions.

---

## 🔍 Debugging

### Enable Detailed Logging
The agent already uses `DEBUG` level logging. Check the log file for:
- LLM prompts and responses
- Pydantic validation results
- Tool execution details
- Memory operations

### Common Issues

**Issue:** "Perception failed"
- **Cause:** LLM returned malformed JSON
- **Solution:** Check PERCEPTION_PROMPT format, review logs

**Issue:** "Tool not found"
- **Cause:** Decision layer requested non-existent tool
- **Solution:** Check available_tools list, update DECISION_PROMPT

**Issue:** "Memory not persisting"
- **Cause:** save_memory() not called or file permissions
- **Solution:** Check logs/ directory permissions

---

## 🎛️ Configuration

### Max Iterations
Edit `agent/ai_agent.py`:
```python
MAX_ITERATIONS = 5  # Change this value
```

### Memory File Location
Edit in `CognitiveAgent.__init__`:
```python
self.memory = MemoryLayer(memory_file="path/to/memory.json")
```

### LLM Model
Edit at top of `agent/ai_agent.py`:
```python
model = genai.GenerativeModel('gemini-2.5-flash')  # Change model here
```

---

## 📝 Extending the Agent

### Add a New Tool
1. Add tool to `server_mcp/mcp_server.py`
2. No changes needed in cognitive layers!
3. Decision layer will automatically see new tool

### Add Custom Thought Type
1. Edit `agent/models.py` - add to `ThoughtType` class
2. Update `PERCEPTION_PROMPT` with example

### Enhance Memory Retrieval
1. Edit `memory.py` - `retrieve_relevant_facts()` method
2. Current: keyword matching
3. Future: vector embeddings (Session 7)

---

## 🔗 Integration with Existing Code

### Flask Server (`server.py`)
✅ Already compatible! The `main()` function signature is unchanged:
```python
result = await ai_main(query)  # Works as before
```

### Chrome Extension
✅ No changes needed! Extension still calls `/api/query`

### MCP Server
✅ No changes! Action layer uses existing MCP tools

---

## 📚 Key Files Reference

| File | Purpose | When to Edit |
|------|---------|-------------|
| `agent/ai_agent.py` | Orchestrator | Adjust iteration logic |
| `agent/perception.py` | Input understanding | Improve perception accuracy |
| `agent/memory.py` | Fact storage | Add memory features |
| `agent/decision.py` | Action planning | Improve decision logic |
| `agent/action.py` | Tool execution | Add new action types |
| `agent/models.py` | Data structures | Add new Pydantic models |
| `agent/prompts.py` | LLM prompts | Tune perception/decision quality |

---

## 🎯 Expected Behavior Changes

### More Iterations?
**Old System:** 1-2 iterations for simple queries
**New System:** May take 1-3 iterations due to layered processing

**Why?** Each layer (Perceive → Remember → Decide → Act) adds structured reasoning

### More Logging?
**Yes!** Each layer logs extensively:
- What it received
- What it's doing
- What it produced

**Benefit:** Much better debugging and traceability

### Memory Between Sessions?
**New Feature!** Agent now remembers facts across sessions via `logs/agent_memory.json`

**Test:**
```bash
# Session 1
python agent/ai_agent.py
> What is 2 + 3?
# Result: 5, memory saved

# Session 2
python agent/ai_agent.py
> What was the last calculation?
# Should retrieve "User calculated 2 + 3 = 5"
```

---

## ✅ Compatibility Checklist

- [x] Flask server still works
- [x] Chrome extension still works
- [x] MCP tools still work
- [x] All existing queries should work (test them!)
- [x] New memory features added
- [x] Better logging and debugging

---

## 🆘 Support

If you encounter issues:

1. Check logs: `logs/cognitive_agent_*.log`
2. Verify memory file: `logs/agent_memory.json`
3. Test with simple query first: "What is 2 + 3?"
4. Check all 4 layers are logging their operations
5. Verify MCP server is running

---

## 🎉 You're Ready!

The cognitive architecture is fully implemented and ready to use. Start with simple queries and observe how each layer processes the information!

**Enjoy your new brain-like AI agent! 🧠✨**

