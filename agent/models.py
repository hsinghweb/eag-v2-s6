"""
Pydantic models for AI agent input and output validation.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal


# Query and Response Models
class QueryInput(BaseModel):
    """Input model for agent queries"""
    query: str = Field(..., min_length=1, description="User query to process")


class AgentResponse(BaseModel):
    """Output model for agent responses"""
    result: str = Field(..., description="Final answer from the agent")
    success: bool = Field(default=True, description="Whether the operation was successful")
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Clean answer without formatting")
    full_response: str = Field(..., description="Full formatted response")


# Conversation History Models
class FunctionCallHistoryItem(BaseModel):
    """Model for function call history items"""
    type: Literal["function_call"] = "function_call"
    name: str = Field(..., description="Function name")
    args: Dict[str, Any] = Field(..., description="Function arguments")
    reasoning_type: str = Field(default="", description="Type of reasoning used")
    step: str = Field(default="", description="Step description")
    result: str = Field(..., description="Function result")


class SelfCheckHistoryItem(BaseModel):
    """Model for self-check history items"""
    type: Literal["self_check"] = "self_check"
    content: str = Field(..., description="Self-check content")


class FallbackHistoryItem(BaseModel):
    """Model for fallback reasoning history items"""
    type: Literal["fallback"] = "fallback"
    content: str = Field(..., description="Fallback content")


# Tool Information Models
class ToolParameter(BaseModel):
    """Model for tool parameter information"""
    name: str
    type: str
    required: bool = True
    description: Optional[str] = None


class ToolInfo(BaseModel):
    """Model for tool information"""
    name: str
    description: str
    parameters: List[ToolParameter] = []


# LLM Response Parsing Models
class FunctionCallRequest(BaseModel):
    """Model for parsed function call requests"""
    name: str = Field(..., description="Function name to call")
    args: Any = Field(..., description="Function arguments (can be list or dict)")
    reasoning_type: str = Field(default="", description="Type of reasoning")
    step: str = Field(default="", description="Step description")


class FinalAnswer(BaseModel):
    """Model for final answer responses"""
    answer: str = Field(..., description="Final answer text")


# Iteration State Models
class IterationState(BaseModel):
    """Model for tracking iteration state"""
    iteration: int = Field(ge=0, le=5, description="Current iteration number")
    max_iterations: int = Field(default=5, ge=1, description="Maximum allowed iterations")
    responses: List[str] = Field(default_factory=list, description="Response history")
    last_response: Optional[Any] = Field(default=None, description="Last response received")


# Tool Execution Models
class ToolCallResult(BaseModel):
    """Model for tool execution results"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class ToolCallRequest(BaseModel):
    """Model for tool call requests"""
    func_name: str
    arguments: Dict[str, Any]
    reasoning_type: str = ""
    step_desc: str = ""


# Configuration Models
class AgentConfig(BaseModel):
    """Configuration for the AI agent"""
    max_iterations: int = Field(default=5, ge=1, le=10, description="Maximum iteration count")
    timeout: int = Field(default=10, ge=1, le=60, description="LLM timeout in seconds")
    model_name: str = Field(default="gemini-2.5-flash", description="LLM model name")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="DEBUG")


# Error Models
class AgentError(BaseModel):
    """Model for agent error responses"""
    success: bool = False
    error: str
    error_type: str
    query: Optional[str] = None


# Prompt Formatting Models
class PromptContext(BaseModel):
    """Model for prompt context data"""
    system_prompt: str
    conversation_history: List[Dict[str, Any]] = []
    query: str
    iteration_responses: List[str] = []
    last_response: Optional[Any] = None


class FormattedPrompt(BaseModel):
    """Model for formatted prompt ready for LLM"""
    content: str
    context: PromptContext

