# Decision Layer Prompt - Side-by-Side Comparison

## BEFORE (Score: 6/8)

```
DECISION_PROMPT = """
You are the Decision-Making Layer of a Math AI Agent. 
Create action plans using available tools.

**User Preferences:** {user_preferences}
**Perception:** {perception}
**Memory:** {memory}
**Available Tools:** {available_tools}

Output JSON with this structure:
{
    "action_plan": [...],
    "reasoning": "overall plan reasoning",
    "expected_outcome": "what should happen",
    "confidence": 0.0-1.0,
    "should_continue": false
}

**Tool Categories:** Arithmetic, Logical Reasoning, Algebra, ...

**Critical Rules:**
1. ALL tool parameters MUST be wrapped in "input" object
2. Use "RESULT_FROM_STEP_N" for result chaining
3. Set should_continue=false when ready to give final answer

Respond with ONLY the JSON object.
"""
```

**Missing:**
- ❌ No self-check instructions
- ❌ No fallback/error handling guidance
- ❌ No explicit responsibility framing

---

## AFTER (Score: 8/8 ✅)

```
DECISION_PROMPT = """
You are the Decision-Making Layer of a Math AI Agent. 
Create action plans using available tools.

**User Preferences:** {user_preferences}
**Perception:** {perception}
**Memory:** {memory}
**Available Tools:** {available_tools}

**Your Responsibilities:**                              ← ✨ NEW
1. Analyze the perception and create a step-by-step action plan
2. Self-verify your plan for correctness and completeness
3. Prepare fallback strategies for potential failures

Output JSON with this structure:
{
    "action_plan": [...],
    "reasoning": "overall plan reasoning",
    "expected_outcome": "what should happen",
    "confidence": 0.0-1.0,
    "should_continue": false,
    
    "self_check": {                                      ← ✨ NEW
        "plan_verified": true|false,
        "tools_available": true|false,
        "parameters_complete": true|false,
        "reasoning": "self-verification explanation"
    },
    
    "fallback_plan": {                                   ← ✨ NEW
        "has_fallback": true|false,
        "fallback_steps": [
            {
                "condition": "when to use this fallback",
                "alternative_action": "what to do instead",
                "tool_name": "alternative tool if applicable or null"
            }
        ],
        "error_handling": "what to do if tools fail"
    }
}

**Tool Categories:** Arithmetic, Logical Reasoning, Algebra, ...

**Critical Rules:**
1. ALL tool parameters MUST be wrapped in "input" object
2. Use "RESULT_FROM_STEP_N" for result chaining
3. Set should_continue=false when ready to give final answer

**Self-Check Instructions:**                            ← ✨ NEW
- ALWAYS verify: Are all required tools available? 
  Are parameters complete? Is the plan logically sound?
- Set plan_verified=false if you detect issues; 
  explain why in reasoning

**Fallback Instructions:**                              ← ✨ NEW
- For tool calls: Provide alternative approaches 
  if the primary tool fails
- For uncertain operations: Specify what to return 
  to the user
- For missing parameters: Define how to request 
  clarification

Respond with ONLY the JSON object.
"""
```

**Added:**
- ✅ Responsibilities section (frames LLM's role)
- ✅ Self-check JSON fields + instructions
- ✅ Fallback plan JSON fields + instructions
- ✅ Error handling guidance
- ✅ Alternative strategy planning

---

## Impact on Evaluation Score

| Criterion | Before | After | Change |
|-----------|--------|-------|--------|
| 1. Explicit Reasoning | ✅ true | ✅ true | - |
| 2. Structured Output | ✅ true | ✅ true | - |
| 3. Tool Separation | ✅ true | ✅ true | - |
| 4. Conversation Loop | ✅ true | ✅ true | - |
| 5. Instructional Framing | ✅ true | ✅ true | - |
| 6. **Internal Self-Checks** | ❌ **false** | ✅ **true** | **FIXED** |
| 7. Reasoning Type Awareness | ✅ true | ✅ true | - |
| 8. **Error Handling/Fallbacks** | ❌ **false** | ✅ **true** | **FIXED** |

**Overall Score: 6/8 → 8/8 (Perfect Score!) 🎉**

---

## Real-World Example

### Query: "Calculate 2+3 and send result via email"

#### BEFORE Response (No Self-Check/Fallback)
```json
{
    "action_plan": [
        {
            "step_number": 1,
            "action_type": "tool_call",
            "tool_name": "add",
            "parameters": {"input": {"a": 2, "b": 3}}
        },
        {
            "step_number": 2,
            "action_type": "tool_call",
            "tool_name": "send_email",
            "parameters": {"input": {"content": "RESULT_FROM_STEP_1"}}
        }
    ],
    "reasoning": "Add numbers then email result",
    "confidence": 0.9,
    "should_continue": false
}
```

**Problem:** If email tool fails, agent has no recovery plan!

#### AFTER Response (With Self-Check/Fallback)
```json
{
    "action_plan": [
        {
            "step_number": 1,
            "action_type": "tool_call",
            "tool_name": "add",
            "parameters": {"input": {"a": 2, "b": 3}}
        },
        {
            "step_number": 2,
            "action_type": "tool_call",
            "tool_name": "send_email",
            "parameters": {"input": {"content": "RESULT_FROM_STEP_1"}}
        }
    ],
    "reasoning": "Add numbers then email result",
    "confidence": 0.9,
    "should_continue": false,
    
    "self_check": {
        "plan_verified": true,
        "tools_available": true,
        "parameters_complete": true,
        "reasoning": "Both 'add' and 'send_email' tools are available. Parameters are complete (a=2, b=3). Email content will use result from step 1."
    },
    
    "fallback_plan": {
        "has_fallback": true,
        "fallback_steps": [
            {
                "condition": "If send_email fails or is unavailable",
                "alternative_action": "Return calculation result to user with message that email could not be sent",
                "tool_name": null
            },
            {
                "condition": "If add tool fails",
                "alternative_action": "Use basic_arithmetic with operation='add'",
                "tool_name": "basic_arithmetic"
            }
        ],
        "error_handling": "If any tool fails, return computed result with explanation of what succeeded and what failed"
    }
}
```

**Benefit:** Agent has clear recovery strategies! ✅

---

## Summary

The enhanced Decision Layer prompt now:

1. **Thinks Before Acting** - Self-verifies the plan
2. **Plans for Failure** - Defines fallback strategies
3. **Communicates Issues** - Explains problems in reasoning
4. **Provides Alternatives** - Multiple paths to success
5. **Handles Errors Gracefully** - User-friendly failure messages

**Result: More robust, reliable, and maintainable AI agent** 🎯

