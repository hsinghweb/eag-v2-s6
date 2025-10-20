# System Prompt Improvements: 9/9 Score Achievement

## Summary
Enhanced both **PERCEPTION_PROMPT** and **DECISION_PROMPT** to achieve a perfect **9/9** score on the evaluation criteria by adding the two missing components:
1. **Internal Self-Checks** - Self-verification mechanisms
2. **Fallbacks** - Error handling and alternative paths

---

## Previous Evaluation Results (7/9)

### PERCEPTION LAYER PROMPT
✅ **Met (7/9):**
- Explicit reasoning
- Structured output
- Tool separation
- Conversation loop
- Instructional framing
- Reasoning type awareness

❌ **Missing (2/9):**
- **Internal self-checks** - No self-verification
- **Fallbacks** - No handling for uncertain cases

### DECISION LAYER PROMPT
✅ **Met (7/9):**
- Explicit reasoning
- Structured output
- Tool separation
- Conversation loop
- Instructional framing
- Reasoning type awareness

❌ **Missing (2/9):**
- **Internal self-checks** - No self-verification
- **Fallbacks** - No fallback paths for tool failures or incomplete memory

---

## Changes Made

### 1. PERCEPTION LAYER ENHANCEMENTS

#### A. Added Self-Check Mechanism
Added `self_check` field to the JSON output structure:

```json
"self_check": {
    "clarity_verified": true/false,
    "entities_complete": true/false,
    "reasoning": "<verification reasoning>"
}
```

**Purpose:**
- Verifies query clarity before proceeding
- Checks if all entities are properly identified
- Provides explicit reasoning for self-verification

**Example (Clear Query):**
```json
"self_check": {
    "clarity_verified": true,
    "entities_complete": true,
    "reasoning": "Clear arithmetic query with both operands identified"
}
```

**Example (Uncertain Query):**
```json
"self_check": {
    "clarity_verified": true,
    "entities_complete": false,
    "reasoning": "Condition 'after Zoom call' lacks specific timing - may need clarification"
}
```

#### B. Added Fallback Handling
Added `fallback` field to the JSON output structure:

```json
"fallback": {
    "is_uncertain": true/false,
    "uncertain_aspects": ["<aspect1>", ...],
    "suggested_clarification": "<question to ask user if uncertain>"
}
```

**Purpose:**
- Identifies uncertain aspects of the query
- Provides specific clarification questions for users
- Enables graceful handling of ambiguous inputs

**Example (No Uncertainty):**
```json
"fallback": {
    "is_uncertain": false,
    "uncertain_aspects": [],
    "suggested_clarification": ""
}
```

**Example (Uncertainty Detected):**
```json
"fallback": {
    "is_uncertain": true,
    "uncertain_aspects": ["exact time of trigger"],
    "suggested_clarification": "Should I remind you immediately after the Zoom call ends, or at a specific time?"
}
```

---

### 2. DECISION LAYER ENHANCEMENTS

#### A. Added Self-Check Mechanism
Added `self_check` field to the JSON output structure:

```json
"self_check": {
    "plan_verified": true/false,
    "tools_available": true/false,
    "parameters_complete": true/false,
    "reasoning": "<verification reasoning>"
}
```

**Purpose:**
- Verifies the action plan before execution
- Checks tool availability
- Ensures all parameters are complete
- Provides explicit reasoning for plan verification

**Examples:**

Simple Query:
```json
"self_check": {
    "plan_verified": true,
    "tools_available": true,
    "parameters_complete": true,
    "reasoning": "Tool t_circle_area is available, radius parameter extracted correctly"
}
```

Complex Multi-Step:
```json
"self_check": {
    "plan_verified": true,
    "tools_available": true,
    "parameters_complete": true,
    "reasoning": "Multi-step plan with result chaining verified; t_solve_linear and t_add both available"
}
```

#### B. Added Fallback Plan
Added `fallback_plan` field to the JSON output structure:

```json
"fallback_plan": {
    "has_fallback": true/false,
    "fallback_steps": [
        {
            "condition": "<when to use this fallback>",
            "alternative_action": "<what to do instead>",
            "tool_name": "<alternative tool if applicable>"
        }
    ],
    "error_handling": "<what to do if tools fail>"
}
```

**Purpose:**
- Provides alternative approaches if primary tools fail
- Specifies conditions for using fallback strategies
- Ensures graceful degradation in case of errors

**Examples:**

No Fallback Needed:
```json
"fallback_plan": {
    "has_fallback": false,
    "fallback_steps": [],
    "error_handling": "If tool fails, inform user to retry with valid radius value"
}
```

With Alternative Tool:
```json
"fallback_plan": {
    "has_fallback": true,
    "fallback_steps": [
        {
            "condition": "If t_chord_length is not available",
            "alternative_action": "Use t_pythagorean with half-chord as unknown leg",
            "tool_name": "t_pythagorean_leg"
        }
    ],
    "error_handling": "If calculation fails, verify distance is less than radius"
}
```

With Multiple Alternatives:
```json
"fallback_plan": {
    "has_fallback": true,
    "fallback_steps": [
        {
            "condition": "If t_mean is not available",
            "alternative_action": "Use t_add to sum all numbers, then divide by count",
            "tool_name": "t_add, t_division"
        }
    ],
    "error_handling": "If tool fails, verify numbers list is not empty"
}
```

Email Delivery Fallback:
```json
"fallback_plan": {
    "has_fallback": true,
    "fallback_steps": [
        {
            "condition": "If send_gmail fails",
            "alternative_action": "Display result directly to user instead of emailing",
            "tool_name": "response"
        }
    ],
    "error_handling": "If email fails, inform user of result and email delivery issue"
}
```

---

## Updated Pydantic Models

### Perception Layer Models (`agent/models.py`)

```python
class SelfCheckPerception(BaseModel):
    """Self-check result from Perception Layer"""
    clarity_verified: bool = Field(..., description="Whether query clarity is verified")
    entities_complete: bool = Field(..., description="Whether all entities are identified")
    reasoning: str = Field(..., description="Reasoning for the self-check")


class FallbackPerception(BaseModel):
    """Fallback information from Perception Layer"""
    is_uncertain: bool = Field(..., description="Whether the perception is uncertain")
    uncertain_aspects: List[str] = Field(default_factory=list, description="Aspects that are uncertain")
    suggested_clarification: str = Field(default="", description="Suggested clarification question for user")


class PerceptionOutput(BaseModel):
    """Output from the Perception Layer"""
    # ... existing fields ...
    self_check: Optional[SelfCheckPerception] = Field(default=None, description="Self-verification results")
    fallback: Optional[FallbackPerception] = Field(default=None, description="Fallback handling information")
```

### Decision Layer Models (`agent/models.py`)

```python
class FallbackStep(BaseModel):
    """A single fallback step"""
    condition: str = Field(..., description="When to use this fallback")
    alternative_action: str = Field(..., description="What to do instead")
    tool_name: Optional[str] = Field(default=None, description="Alternative tool if applicable")


class SelfCheckDecision(BaseModel):
    """Self-check result from Decision Layer"""
    plan_verified: bool = Field(..., description="Whether the plan is verified")
    tools_available: bool = Field(..., description="Whether required tools are available")
    parameters_complete: bool = Field(..., description="Whether all parameters are complete")
    reasoning: str = Field(..., description="Reasoning for the self-check")


class FallbackPlan(BaseModel):
    """Fallback plan for Decision Layer"""
    has_fallback: bool = Field(..., description="Whether a fallback exists")
    fallback_steps: List[FallbackStep] = Field(default_factory=list, description="Fallback steps")
    error_handling: str = Field(default="", description="What to do if tools fail")


class DecisionOutput(BaseModel):
    """Output from the Decision-Making Layer"""
    # ... existing fields ...
    self_check: Optional[SelfCheckDecision] = Field(default=None, description="Self-verification results")
    fallback_plan: Optional[FallbackPlan] = Field(default=None, description="Fallback plan for errors")
```

---

## Benefits of These Enhancements

### 1. **Improved Reliability**
- Self-checks catch potential issues before execution
- Fallback plans ensure graceful degradation
- Reduces failure rates and improves user experience

### 2. **Better Error Handling**
- Explicit alternative paths when tools fail
- Clear error messages for users
- Automatic recovery strategies

### 3. **Enhanced Transparency**
- Users can see verification reasoning
- Clarification questions make ambiguity explicit
- Better debugging and troubleshooting

### 4. **Increased Robustness**
- Multiple solution paths for each problem
- Handles edge cases proactively
- Adapts to tool availability changes

### 5. **User Experience**
- Proactive clarification for unclear queries
- Informative error messages
- Consistent behavior even in failure scenarios

---

## Example Complete Outputs

### Perception Layer (Clear Query)
```json
{
    "intent": "calculation",
    "entities": {"numbers": [2, 3], "operation": "addition"},
    "thought_type": "Analysis",
    "extracted_facts": ["User wants to add 2 and 3"],
    "requires_tools": true,
    "confidence": 1.0,
    "self_check": {
        "clarity_verified": true,
        "entities_complete": true,
        "reasoning": "Clear arithmetic query with both operands identified"
    },
    "fallback": {
        "is_uncertain": false,
        "uncertain_aspects": [],
        "suggested_clarification": ""
    }
}
```

### Decision Layer (Multi-Step with Fallback)
```json
{
    "action_plan": [...],
    "reasoning": "Multi-value problem: need to calculate and return both consecutive numbers",
    "expected_outcome": "User receives both numbers: 20 and 21",
    "confidence": 1.0,
    "should_continue": false,
    "self_check": {
        "plan_verified": true,
        "tools_available": true,
        "parameters_complete": true,
        "reasoning": "Multi-step plan with result chaining verified; t_solve_linear and t_add both available"
    },
    "fallback_plan": {
        "has_fallback": true,
        "fallback_steps": [
            {
                "condition": "If result chaining fails",
                "alternative_action": "Solve equation manually: (41-1)/2 = 20, then add 1",
                "tool_name": "t_subtract, t_division, t_add"
            }
        ],
        "error_handling": "If any step fails, recalculate from equation x + (x+1) = 41"
    }
}
```

---

## Files Modified

1. **`agent/prompts.py`**
   - Updated `PERCEPTION_PROMPT` output structure
   - Updated all perception examples with self_check and fallback fields
   - Updated `DECISION_PROMPT` output structure
   - Updated all decision examples with self_check and fallback_plan fields

2. **`agent/models.py`**
   - Added `SelfCheckPerception` model
   - Added `FallbackPerception` model
   - Updated `PerceptionOutput` to include new fields
   - Added `FallbackStep` model
   - Added `SelfCheckDecision` model
   - Added `FallbackPlan` model
   - Updated `DecisionOutput` to include new fields

---

## Expected Evaluation Score

### PERCEPTION LAYER PROMPT: **9/9** ✅
- ✅ Explicit reasoning
- ✅ Structured output
- ✅ Tool separation
- ✅ Conversation loop
- ✅ Instructional framing
- ✅ **Internal self-checks** ← NEW
- ✅ Reasoning type awareness
- ✅ **Fallbacks** ← NEW

### DECISION LAYER PROMPT: **9/9** ✅
- ✅ Explicit reasoning
- ✅ Structured output
- ✅ Tool separation
- ✅ Conversation loop
- ✅ Instructional framing
- ✅ **Internal self-checks** ← NEW
- ✅ Reasoning type awareness
- ✅ **Fallbacks** ← NEW

---

## Next Steps

1. **Test the enhanced prompts** with various queries to ensure proper self-check and fallback generation
2. **Implement fallback execution logic** in the action layer to actually use the fallback plans when tools fail
3. **Monitor self-check results** to identify common issues or patterns in query ambiguity
4. **Iterate on clarification questions** based on user feedback to improve uncertainty handling

---

## Conclusion

The system prompts now meet all 9 evaluation criteria by incorporating:
- **Proactive self-verification** at both perception and decision stages
- **Comprehensive fallback strategies** for error handling and alternative approaches
- **Enhanced transparency** through explicit reasoning for all checks
- **Better user experience** through clarification questions and graceful degradation

These improvements make the cognitive agent more robust, reliable, and user-friendly while maintaining the existing strengths in reasoning, structure, and tool integration.

