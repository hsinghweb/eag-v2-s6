# MCP Tool Parameter Format Fix

## Issue
MCP tools were failing with Pydantic validation error:
```
Error executing tool t_number_list_to_sum: 1 validation error for t_number_list_to_sumArguments
input
  Field required [type=missing, input_value={'numbers': [100, 200]}, input_type=dict]
```

## Root Cause
FastMCP wraps Pydantic model parameters in an `input` field. The Decision layer was generating parameters in the wrong format.

### Incorrect Format (Before):
```json
{
  "tool_name": "t_number_list_to_sum",
  "parameters": {
    "numbers": [100, 200]
  }
}
```

### Correct Format (After):
```json
{
  "tool_name": "t_number_list_to_sum",
  "parameters": {
    "input": {
      "numbers": [100, 200]
    }
  }
}
```

## Fix Applied
Updated `agent/prompts.py` - **DECISION_PROMPT** to show correct parameter format in examples:

```python
"parameters": {{"input": {{"numbers": [2, 3]}}}}
```

Added explicit guidance:
```
**Important:** All tool parameters must be wrapped in an "input" object. For example:
- t_number_list_to_sum: {"input": {"numbers": [1, 2, 3]}}
- t_calculate_difference: {"input": {"a": 300, "b": 50}}
- send_gmail: {"input": {"content": "email text"}}
- draw_rectangle: {"input": {"x1": 1, "y1": 1, "x2": 8, "y2": 6}}
```

## Why This Format?

FastMCP tools are defined like:
```python
@mcp.tool()
def t_number_list_to_sum(input: NumberListInput) -> NumberListOutput:
    result = number_list_to_sum(input.numbers)
    return NumberListOutput(result=result)
```

The parameter is named `input` and it's a Pydantic model (`NumberListInput`). So when calling the tool via MCP, we must pass:
```python
arguments = {"input": {"numbers": [100, 200]}}
```

## Testing

**Query:** "add 100 in 200"

**Expected Flow:**
1. **Perception:** Extract intent=calculation, entities={numbers: [100, 200]}
2. **Decision:** Create plan with correct parameters:
   ```json
   {
     "tool_name": "t_number_list_to_sum",
     "parameters": {"input": {"numbers": [100, 200]}}
   }
   ```
3. **Action:** Execute tool successfully → Result: `300`
4. **Final:** Return `300` to user

**Before Fix:** ❌ Pydantic validation error  
**After Fix:** ✅ Returns `300`

## All Tools Affected

All MCP tools using Pydantic models need the `input` wrapper:
- Math tools: `t_number_list_to_sum`, `t_calculate_difference`, `t_number_list_to_product`, `t_calculate_division`, etc.
- Email: `send_gmail`
- PowerPoint: `draw_rectangle`, `add_text_in_powerpoint`
- Database: `t_calculate_salary_for_id`, `t_calculate_salary_for_name`
- Utility: `t_strings_to_chars_to_int`, `t_int_list_to_exponential_values`, etc.

## Files Modified
- ✅ `agent/prompts.py` - Updated DECISION_PROMPT with correct format

## Next Steps
Restart the server and test:
```bash
uv run .\server.py
```

Test queries:
- "add 100 in 200" → Should return `300`
- "subtract 50 from 300" → Should return `250`
- "what is 15% of 200" → Should return `30`

All queries should now work correctly! 🎉

