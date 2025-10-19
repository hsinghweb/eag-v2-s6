"""
Pydantic models for input and output validation of MCP tools.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional


# PowerPoint Tool Models
class DrawRectangleInput(BaseModel):
    """Input model for drawing rectangles in PowerPoint"""
    x1: int = Field(default=1, ge=1, le=8, description="X-coordinate of top-left corner")
    y1: int = Field(default=1, ge=1, le=8, description="Y-coordinate of top-left corner")
    x2: int = Field(default=8, ge=1, le=8, description="X-coordinate of bottom-right corner")
    y2: int = Field(default=6, ge=1, le=8, description="Y-coordinate of bottom-right corner")
    
    @validator('x2')
    def x2_must_be_greater_than_x1(cls, v, values):
        if 'x1' in values and v <= values['x1']:
            raise ValueError('x2 must be greater than x1')
        return v
    
    @validator('y2')
    def y2_must_be_greater_than_y1(cls, v, values):
        if 'y1' in values and v <= values['y1']:
            raise ValueError('y2 must be greater than y1')
        return v


class DrawRectangleOutput(BaseModel):
    """Output model for draw rectangle operation"""
    success: bool
    message: str


class AddTextInput(BaseModel):
    """Input model for adding text in PowerPoint"""
    text: str = Field(..., min_length=1, description="Text to add to the slide")


class AddTextOutput(BaseModel):
    """Output model for add text operation"""
    success: bool
    message: str


class PowerPointOperationOutput(BaseModel):
    """Generic output model for PowerPoint operations"""
    success: bool
    message: str


# Email Tool Models
class SendGmailInput(BaseModel):
    """Input model for sending Gmail"""
    content: str = Field(..., min_length=1, description="Email content to send")


class SendGmailOutput(BaseModel):
    """Output model for send Gmail operation"""
    success: bool
    message: str
    recipient: Optional[str] = None


# Math Tool Models
class NumberListInput(BaseModel):
    """Input model for list-based math operations"""
    numbers: List[float] = Field(..., min_items=1, description="List of numbers")


class NumberListOutput(BaseModel):
    """Output model for list-based math operations"""
    result: float


class TwoNumberInput(BaseModel):
    """Input model for two-number operations"""
    a: float = Field(..., description="First number")
    b: float = Field(..., description="Second number")


class TwoNumberOutput(BaseModel):
    """Output model for two-number operations"""
    result: float


class SingleNumberInput(BaseModel):
    """Input model for single-number operations"""
    value: float = Field(..., description="Input number")


class SingleNumberOutput(BaseModel):
    """Output model for single-number operations"""
    result: float


class PercentageInput(BaseModel):
    """Input model for percentage calculation"""
    percent: float = Field(..., ge=0, description="Percentage value")
    number: float = Field(..., description="Base number")


class PercentageOutput(BaseModel):
    """Output model for percentage calculation"""
    result: float


class StringToCharsInput(BaseModel):
    """Input model for converting string to ASCII values"""
    text: str = Field(..., min_length=1, description="Input string")


class StringToCharsOutput(BaseModel):
    """Output model for string to ASCII conversion"""
    ascii_values: List[int]


class ExponentialInput(BaseModel):
    """Input model for exponential operations"""
    numbers: List[float] = Field(..., min_items=1, description="List of numbers for exponential")


class ExponentialOutput(BaseModel):
    """Output model for exponential operations"""
    values: List[float]


class FibonacciInput(BaseModel):
    """Input model for Fibonacci sequence"""
    n: int = Field(..., ge=0, description="Number of Fibonacci numbers to generate")


class FibonacciOutput(BaseModel):
    """Output model for Fibonacci sequence"""
    sequence: List[int]


class FactorialInput(BaseModel):
    """Input model for factorial calculation"""
    n: int = Field(..., ge=0, description="Number for factorial calculation")


class FactorialOutput(BaseModel):
    """Output model for factorial calculation"""
    factorials: List[int]


class PermutationInput(BaseModel):
    """Input model for permutation calculation"""
    n: int = Field(..., ge=0, description="Total number of items")
    r: int = Field(..., ge=0, description="Number of items to arrange")
    
    @validator('r')
    def r_must_not_exceed_n(cls, v, values):
        if 'n' in values and v > values['n']:
            raise ValueError('r cannot be greater than n')
        return v


class PermutationOutput(BaseModel):
    """Output model for permutation calculation"""
    result: int


class CombinationInput(BaseModel):
    """Input model for combination calculation"""
    n: int = Field(..., ge=0, description="Total number of items")
    r: int = Field(..., ge=0, description="Number of items to select")
    
    @validator('r')
    def r_must_not_exceed_n(cls, v, values):
        if 'n' in values and v > values['n']:
            raise ValueError('r cannot be greater than n')
        return v


class CombinationOutput(BaseModel):
    """Output model for combination calculation"""
    result: int


class EmployeeIdInput(BaseModel):
    """Input model for employee salary lookup by ID"""
    emp_id: int = Field(..., ge=1, description="Employee ID")


class EmployeeNameInput(BaseModel):
    """Input model for employee salary lookup by name"""
    emp_name: str = Field(..., min_length=1, description="Employee name")


class SalaryOutput(BaseModel):
    """Output model for salary queries"""
    salary: Optional[float]
    found: bool


class FallbackInput(BaseModel):
    """Input model for fallback reasoning"""
    description: str = Field(..., min_length=1, description="Description of the fallback situation")


class FallbackOutput(BaseModel):
    """Output model for fallback reasoning"""
    message: str

