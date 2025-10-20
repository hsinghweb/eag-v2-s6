# Iteration Counting Update

## Change Summary

Updated the iteration counting logic to count **each individual LLM call or tool call** as one iteration, instead of counting a full cognitive loop as one iteration.

## Previous Behavior

**Before**: One complete cognitive cycle (Perception → Memory → Decision → Action execution) = 1 iteration

Example for query "add 2 and 3":
```
ITERATION 1/5
  - Perception (LLM call)
  - Memory retrieval
  - Decision (LLM call)
  - Action: t_number_list_to_sum (tool call)
  - Action: response

Result: Completed in 1 iteration
```

## New Behavior

**After**: Each LLM call and each tool call = 1 iteration

Example for query "add 2 and 3":
```
COGNITIVE LOOP 1
  ITERATION 1/50: Perception Layer (LLM Call)
  ✓ Iteration 1 complete: Perception
  
  ITERATION 2/50: Decision Layer (LLM Call)
  ✓ Iteration 2 complete: Decision (2 actions planned)
  
  ITERATION 3/50: Action Step 1 - t_number_list_to_sum
  ✓ Iteration 3 complete: t_number_list_to_sum
  
  Executing action 2: Return the result to user (no iteration count)

Result: Completed in 3 iterations
  - Perception LLM calls: 1
  - Decision LLM calls: 1
  - Tool calls: 1
```

## What Counts as an Iteration

| Operation | Counts as Iteration? | Reason |
|-----------|---------------------|---------|
| Perception LLM call | ✅ Yes | Calls Gemini LLM |
| Memory retrieval | ❌ No | Just searches in-memory data |
| Decision LLM call | ✅ Yes | Calls Gemini LLM |
| Tool call (e.g., t_add, t_solve_linear) | ✅ Yes | External computation/operation |
| Response action | ❌ No | Just formatting final response |

## Implementation Details

### File: `agent/ai_agent.py`

**Line 62**: Increased MAX_ITERATIONS from 5 to 50
```python
MAX_ITERATIONS = 50  # Each LLM call or tool call counts as one iteration
```

**Lines 252-382**: Restructured cognitive loop
- Added `cognitive_loop_count` to track full loops separately
- Increment iteration counter before each LLM call
- Increment iteration counter before each tool call
- Added clear logging for each iteration

### Logging Format

**Cognitive Loop Header**:
```
================================================================================
[AGENT] COGNITIVE LOOP 1
================================================================================
```

**Iteration Header**:
```
--------------------------------------------------------------------------------
[AGENT] ITERATION 3/50: Action Step 1 - t_number_list_to_sum
--------------------------------------------------------------------------------
```

**Iteration Completion**:
```
[AGENT] ✓ Iteration 3 complete: t_number_list_to_sum
```

### Final Summary

At completion, the agent now logs:
```
================================================================================
[AGENT] Agent completed successfully
Total Iterations: 3
  - Perception LLM calls: 1
  - Decision LLM calls: 1
  - Tool calls: 1
Result: 5
================================================================================
```

## Example Scenarios

### Simple Query: "What is 2 + 3?"

**Iterations**:
1. Perception (LLM)
2. Decision (LLM)
3. t_number_list_to_sum (tool)

**Total**: 3 iterations

### Complex Query: "Two consecutive numbers sum to 41. What are they?"

**Iterations**:
1. Perception (LLM)
2. Decision (LLM)
3. t_solve_linear (tool) - solves 2x + 1 = 41
4. t_add (tool) - adds 1 to get second number

**Total**: 4 iterations

### Email Query: "add 2 and 3 and send result to email"

**Iterations**:
1. Perception (LLM)
2. Decision (LLM)
3. t_add (tool) - calculates 2 + 3
4. send_gmail (tool) - sends email

**Total**: 4 iterations

### Logical Query: "evaluate true AND false and send result to email"

**Iterations**:
1. Perception (LLM)
2. Decision (LLM)
3. t_logical_and (tool) - evaluates logical expression
4. send_gmail (tool) - sends email

**Total**: 4 iterations

## Benefits

1. **Transparency**: Users can see exactly how many LLM calls and tool calls are being made
2. **Cost Tracking**: Each LLM call has a cost, so this helps track resource usage
3. **Performance Monitoring**: Easier to identify bottlenecks
4. **Debugging**: Clear visibility into which step is being executed
5. **Accurate Counting**: Reflects actual computational work being done

## Iteration Limit

**MAX_ITERATIONS = 50**

This is sufficient for:
- Complex multi-step problems (10-20 steps)
- Problems requiring multiple cognitive loops
- Error recovery and retries

Most queries complete in 3-10 iterations:
- Simple arithmetic: 3 iterations
- Equation solving: 3-4 iterations
- Multi-step word problems: 4-8 iterations
- Complex statistical analysis: 5-15 iterations

## Backward Compatibility

✅ No breaking changes to:
- API endpoints
- Input/output formats
- Tool signatures
- Memory structure
- Existing functionality

Only change is in logging verbosity and iteration counting logic.

## Files Modified

1. **agent/ai_agent.py**
   - Line 62: Updated MAX_ITERATIONS constant
   - Lines 241-243: Added iteration info to startup log
   - Lines 252-382: Restructured cognitive loop with new iteration counting
   - Lines 456-470: Added iteration breakdown to completion summary

## Future Enhancements

Potential improvements:
1. Track LLM call costs per iteration
2. Add iteration time tracking
3. Export iteration metrics to monitoring dashboard
4. Add iteration budget per user/session
5. Optimize to reduce unnecessary LLM calls

## Testing

Test with various query types to verify iteration counts:

```python
# Test 1: Simple arithmetic
Query: "What is 5 + 3?"
Expected Iterations: 3 (1 perception, 1 decision, 1 tool)

# Test 2: Multi-step
Query: "Solve x + 4 = 9, then add 2 to the result"
Expected Iterations: 4 (1 perception, 1 decision, 2 tools)

# Test 3: With email
Query: "Calculate area of circle with radius 5 and email the result"
Expected Iterations: 4 (1 perception, 1 decision, 2 tools)
```

## Monitoring

Check logs for:
- `[AGENT] ITERATION X/50:` - tracks each iteration
- `Total Iterations: X` - summary at completion
- Breakdown of LLM vs tool calls

This provides full visibility into agent execution.

