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
    
    def __init__(self, session: ClientSession, tools: list):
        """
        Initialize the Cognitive Agent.
        
        Args:
            session: MCP client session
            tools: Available MCP tools
        """
        self.session = session
        self.tools = tools
        
        # Initialize cognitive layers
        self.perception = PerceptionLayer(model)
        self.memory = MemoryLayer(memory_file="logs/agent_memory.json")
        self.decision = DecisionLayer(model)
        self.action = ActionLayer(session, tools)
        
        # Initialize cognitive state
        self.state = CognitiveState()
        
        logger.info("[AGENT] Cognitive Agent initialized with 4 layers")
    
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
                for action_step in decision.action_plan:
                    logger.info(f"\n[AGENT] Executing action {action_step.step_number}: {action_step.description}")
                    
                    action_result = await self.action.execute(action_step)
                    self.state.action_results.append(action_result)
                    
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
            if final_result is None:
                # No explicit final result - compile from action results
                successful_results = [
                    str(ar.result) for ar in self.state.action_results 
                    if ar.success and ar.result is not None
                ]
                final_result = " | ".join(successful_results) if successful_results else "Task completed"
            
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


async def main(query: str):
    """
    Main entry point for the cognitive agent.
    
    Args:
        query: User query string
        
    Returns:
        JSON string with agent response
    """
    logger.info(f"Starting cognitive agent with query: {query}")
    
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
                agent = CognitiveAgent(session, tools)
                
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
