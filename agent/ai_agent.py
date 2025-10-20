"""
AI Agent with Cognitive Layers Architecture

This module orchestrates the 4 cognitive layers:
👁️ Perception → 🧠 Memory → 🧭 Decision → 🎯 Action

The agent no longer functions as a single "Augmented LLM" but as a
structured, layered cognitive system with clear separation of concerns.
"""
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import google.generativeai as genai
import logging
from datetime import datetime
import traceback
from typing import Optional, Dict, Any

# Import cognitive layers
from .perception import PerceptionLayer
from .memory import MemoryLayer
from .decision import DecisionLayer
from .action import ActionLayer

# Import models
from .models import (
    AgentResponse,
    CognitiveState,
    MemoryQuery
)

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"cognitive_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY not found in .env file")
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Constants
MAX_ITERATIONS = 5


class CognitiveAgent:
    """
    Cognitive Agent with 4-layer architecture.
    
    This agent processes queries through distinct cognitive layers:
    1. Perception: Understanding input
    2. Memory: Storing and retrieving context
    3. Decision: Planning actions
    4. Action: Executing the plan
    """
    
    def __init__(self, session: ClientSession, tools: list, preferences: Optional[Dict[str, Any]] = None, memory_file: Optional[str] = None):
        """
        Initialize the Cognitive Agent.
        
        Args:
            session: MCP client session
            tools: Available MCP tools
            preferences: User preferences (math ability, location, etc.)
            memory_file: Path to memory file (if None, creates a timestamped one)
        """
        self.session = session
        self.tools = tools
        self.preferences = preferences or {}
        
        # Create timestamped memory file if not provided
        if memory_file is None:
            memory_file = os.path.join(log_dir, f"agent_memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Initialize cognitive layers
        self.perception = PerceptionLayer(model, user_preferences=self.preferences)
        self.memory = MemoryLayer(memory_file=memory_file)
        self.decision = DecisionLayer(model, user_preferences=self.preferences)
        self.action = ActionLayer(session, tools)
        
        # Store user preferences in memory
        if self.preferences:
            self._store_preferences()
        
        # Initialize cognitive state
        self.state = CognitiveState()
        
        logger.info("[AGENT] Cognitive Agent initialized with 4 layers")
        logger.info(f"[AGENT] Memory file: {memory_file}")
        if self.preferences:
            logger.info(f"[AGENT] User preferences loaded: {self.preferences}")
    
    def _store_preferences(self):
        """
        Store user preferences in the Memory Layer.
        """
        # Store each preference as a fact
        for key, value in self.preferences.items():
            preference_text = f"User preference: {key} = {value}"
            self.memory.store_fact(
                content=preference_text,
                source="user_preferences",
                relevance_score=1.0
            )
        
        # Store in user_preferences dict (always update to ensure proper capture)
        for key, value in self.preferences.items():
            self.memory.memory_state.user_preferences[key] = value
        
        logger.info(f"[AGENT] Stored {len(self.preferences)} user preferences in memory")
    
    def _replace_result_placeholders(self, params: dict, results_map: dict) -> dict:
        """
        Replace result placeholders like 'RESULT_FROM_STEP_1' with actual values.
        
        Args:
            params: Parameters dict that may contain placeholders
            results_map: Map of step_number -> result value
            
        Returns:
            Updated parameters with placeholders replaced
        """
        import json
        import re
        import copy
        
        # Deep copy to avoid modifying original
        params_copy = copy.deepcopy(params)
        
        def replace_in_value(value, param_name=None):
            if isinstance(value, str):
                # Check for result placeholder patterns
                match = re.search(r'RESULT_FROM_STEP_(\d+)', value)
                if match:
                    step_num = int(match.group(1))
                    if step_num in results_map:
                        result = results_map[step_num]
                        
                        # Determine if we need string or numeric output
                        # Parameters like 'content', 'text', 'message' should be strings
                        needs_string = param_name and param_name.lower() in ['content', 'text', 'message', 'body', 'description']
                        
                        # Try to extract value from result
                        extracted_value = None
                        if isinstance(result, (int, float)):
                            extracted_value = result
                        elif isinstance(result, str):
                            try:
                                # Try to parse as JSON
                                parsed = json.loads(result)
                                # Extract value from common fields
                                for key in ['solution', 'result', 'value', 'answer']:
                                    if key in parsed and parsed[key] is not None:
                                        extracted_value = float(parsed[key])
                                        break
                            except:
                                # Try to extract number directly
                                num_match = re.search(r'-?\d+\.?\d*', result)
                                if num_match:
                                    extracted_value = float(num_match.group())
                        
                        # Return appropriate format
                        if extracted_value is not None:
                            if needs_string:
                                # Format nicely for text output
                                if isinstance(extracted_value, float) and extracted_value.is_integer():
                                    return f"The result is: {int(extracted_value)}"
                                else:
                                    return f"The result is: {extracted_value}"
                            else:
                                # Return numeric value for calculations
                                return extracted_value
                        
                        return result
            elif isinstance(value, dict):
                return {k: replace_in_value(v, k) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_in_value(item) for item in value]
            return value
        
        return replace_in_value(params_copy)
    
    async def process_query(self, query: str) -> AgentResponse:
        """
        Process a user query through the cognitive layers.
        
        Flow:
        1. 👁️ PERCEIVE: Extract intent, entities, facts
        2. 🧠 REMEMBER: Store facts, retrieve relevant context
        3. 🧭 DECIDE: Create action plan
        4. 🎯 ACT: Execute actions
        5. Repeat if needed
        
        Args:
            query: User query string
            
        Returns:
            AgentResponse: Final response with result
        """
        logger.info("=" * 80)
        logger.info(f"[AGENT] Starting cognitive processing for: {query}")
        logger.info("=" * 80)
        
        try:
            # Reset state for new query
            self.state = CognitiveState()
            final_result = None
            
            # Store initial query in memory context
            self.memory.update_context("initial_query", query)
            
            # Cognitive loop
            while self.state.iteration < MAX_ITERATIONS:
                self.state.iteration += 1
                logger.info("\n" + "-" * 80)
                logger.info(f"[AGENT] ITERATION {self.state.iteration}/{MAX_ITERATIONS}")
                logger.info("-" * 80)
                
                # ============================================================
                # LAYER 1: PERCEPTION 👁️
                # ============================================================
                if self.state.perception is None:
                    # First iteration - perceive the query
                    perception = await self.perception.perceive(query)
                    self.state.perception = perception
                    
                    # Store extracted facts in memory
                    if perception.extracted_facts:
                        self.memory.store_facts(perception.extracted_facts, source="perception")
                else:
                    # Subsequent iterations - use existing perception
                    perception = self.state.perception
                
                # ============================================================
                # LAYER 2: MEMORY 🧠
                # ============================================================
                # Retrieve relevant memories
                memory_query = MemoryQuery(
                    query=query,
                    max_results=5,
                    min_relevance=0.3
                )
                memory_retrieval = self.memory.retrieve_relevant_facts(memory_query)
                
                # ============================================================
                # LAYER 3: DECISION 🧭
                # ============================================================
                # Get available tools
                available_tools = self.action.get_available_tools()
                
                # Make decision
                decision = await self.decision.decide(
                    perception=perception,
                    memory=memory_retrieval,
                    available_tools=available_tools,
                    previous_actions=None  # Simplified for now
                )
                self.state.decision = decision
                
                # ============================================================
                # LAYER 4: ACTION 🎯
                # ============================================================
                # Execute each action in the plan
                # Keep track of results for chaining
                action_results_map = {}
                
                for action_step in decision.action_plan:
                    logger.info(f"\n[AGENT] Executing action {action_step.step_number}: {action_step.description}")
                    
                    # Replace result placeholders in parameters
                    if action_step.parameters:
                        action_step.parameters = self._replace_result_placeholders(
                            action_step.parameters, 
                            action_results_map
                        )
                    
                    action_result = await self.action.execute(action_step)
                    self.state.action_results.append(action_result)
                    
                    # Store result for future steps
                    if action_result.success and action_result.result is not None:
                        action_results_map[action_step.step_number] = action_result.result
                    
                    # Store action facts in memory
                    if action_result.success and action_result.facts_to_remember:
                        self.memory.store_facts(action_result.facts_to_remember, source="action")
                    
                    # Check if this is a response action (final answer)
                    if action_step.action_type == "response" and action_result.success:
                        final_result = action_result.result
                        logger.info(f"[AGENT] Final result obtained: {final_result}")
                
                # ============================================================
                # CHECK FOR COMPLETION
                # ============================================================
                if not decision.should_continue or final_result is not None:
                    self.state.complete = True
                    logger.info("[AGENT] Cognitive processing complete")
                    break
                
                logger.info(f"[AGENT] Continuing to iteration {self.state.iteration + 1}...")
            
            # ============================================================
            # FINALIZATION
            # ============================================================
            # Extract actual computed values from tool executions
            # Exclude non-mathematical tools from result display
            NON_MATH_TOOLS = ['send_gmail', 'draw_rectangle', 'add_text_in_powerpoint']
            
            tool_results = []
            tool_results_parsed = []
            if self.state.decision and self.state.decision.action_plan:
                for i, ar in enumerate(self.state.action_results):
                    if ar.success and ar.result is not None:
                        # Get the corresponding action step to check type
                        if i < len(self.state.decision.action_plan):
                            action_step = self.state.decision.action_plan[i]
                            # Only include tool_call results that are mathematical computations
                            # Exclude email/powerpoint/presentation tools
                            if action_step.action_type == "tool_call" and action_step.tool_name not in NON_MATH_TOOLS:
                                result_str = str(ar.result)
                                tool_results.append(result_str)
                                
                                # Try to parse JSON results to extract actual values
                                try:
                                    import json
                                    import re
                                    # Handle various JSON formats
                                    if result_str.strip().startswith('{'):
                                        parsed = json.loads(result_str)
                                        # Extract numeric values from common fields
                                        for key in ['solution', 'result', 'value', 'answer']:
                                            if key in parsed and parsed[key] is not None:
                                                tool_results_parsed.append(float(parsed[key]))
                                                break
                                    else:
                                        # Try to extract number directly
                                        num_match = re.search(r'-?\d+\.?\d*', result_str)
                                        if num_match:
                                            tool_results_parsed.append(float(num_match.group()))
                                except:
                                    pass
            
            # Build final result from tool executions
            if tool_results_parsed and len(tool_results_parsed) > 1:
                # Multiple numeric results - format nicely
                final_result = ", ".join([str(v) for v in tool_results_parsed])
                logger.info(f"[AGENT] Using multiple computed results: {final_result}")
            elif tool_results:
                # Use the last tool result
                final_result = tool_results[-1] if len(tool_results) == 1 else " | ".join(tool_results)
                logger.info(f"[AGENT] Using computed result: {final_result}")
            elif final_result is None:
                # No results at all
                final_result = "Task completed"
            
            # Save memory to disk
            self.memory.save_memory()
            
            # Create response
            response = AgentResponse(
                result=final_result,
                success=True,
                query=query,
                answer=final_result,
                full_response=f"Query: {query}\nResult: {final_result}"
            )
            
            logger.info("=" * 80)
            logger.info("[AGENT] Agent completed successfully")
            logger.info(f"Result: {final_result}")
            logger.info("=" * 80 + "\n")
            
            return response
            
        except Exception as e:
            logger.error(f"[AGENT] Error in cognitive processing: {e}")
            logger.error(traceback.format_exc())
            
            # Return error response
            return AgentResponse(
                result=f"Error: {str(e)}",
                success=False,
                query=query,
                answer=f"I encountered an error: {str(e)}",
                full_response=f"Query: {query}\nError: {str(e)}"
            )


async def main(query: str, preferences: Optional[Dict[str, Any]] = None):
    """
    Main entry point for the cognitive agent.
    
    Args:
        query: User query string
        preferences: Dictionary of user preferences (e.g., math ability, location, etc.)
        
    Returns:
        JSON string with agent response
    """
    logger.info(f"Starting cognitive agent with query: {query}")
    if preferences:
        logger.info(f"User preferences: {preferences}")
    
    try:
        # Establish MCP connection
        logger.info("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["server_mcp/mcp_server.py", "dev"]
        )

        async with stdio_client(server_params) as (read, write):
            logger.info("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                logger.info("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                logger.info("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                logger.info(f"Successfully retrieved {len(tools)} tools")
                
                # Create cognitive agent
                agent = CognitiveAgent(session, tools, preferences=preferences)
                
                # Process query
                response = await agent.process_query(query)
                
                # Return JSON response
                return response.model_dump_json(indent=2)
                
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    query = input("Enter your query: ").strip()
    if not query:
        logger.error("No query provided by user")
        print("Error: Please provide a valid query")
    else:
        logger.info(f"User provided query: {query}")
        result = asyncio.run(main(query))
        if result:
            print(f"\n{'='*80}")
            print("RESULT:")
            print(result)
            print(f"{'='*80}")
