import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from agent.ai_agent import main as ai_main

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/query', methods=['POST'])
async def handle_query():
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        logger.info(f"Received query: {query}")
        
        # Run the AI agent with the query
        result = await ai_main(query)
        
        # Handle None result (agent failed or timed out)
        if result is None:
            logger.error("Agent returned None - possible timeout or error")
            return jsonify({
                'status': 'error',
                'message': 'Agent failed to process query. Check logs for details.'
            }), 500
        
        # Parse the JSON response from the AI agent (Pydantic model output)
        try:
            if isinstance(result, str):
                import json
                result_data = json.loads(result)
                logger.debug(f"Parsed result data: {result_data}")
                
                # Pydantic AgentResponse model has these fields:
                # result, success, query, answer, full_response
                if 'result' in result_data and result_data.get('success', True):
                    # Return the clean result for the Chrome extension
                    return jsonify({
                        'status': 'success',
                        'result': result_data.get('answer', result_data['result']),
                        'query': result_data.get('query', query)
                    })
                elif not result_data.get('success', True):
                    # Handle error responses
                    return jsonify({
                        'status': 'error',
                        'message': result_data.get('result', 'Unknown error')
                    }), 500
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI agent response as JSON: {e}")
            logger.error(f"Raw result: {result}")
            # Fallback to string extraction if JSON parsing fails
            if isinstance(result, str) and 'FINAL_ANSWER:' in result:
                final_answer = result.split('FINAL_ANSWER:')[-1].strip('[] \'"')
                # Clean up any Query/Result prefixes
                if 'Query:' in final_answer:
                    final_answer = final_answer.split('Result:')[-1].strip()
                return jsonify({
                    'status': 'success',
                    'result': final_answer,
                    'query': query
                })
        
        # If we get here, we couldn't extract a proper result
        logger.error(f"Unexpected result format: {result}")
        return jsonify({
            'status': 'error',
            'message': 'Unexpected response format from agent',
            'raw_result': str(result) if result else 'None'
        }), 500
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Make sure the server is accessible from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=True)
