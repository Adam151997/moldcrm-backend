"""
AI Agent Service - Handles multi-turn conversations with function calling
Uses Gemini 2.5 Flash with function calling to enable conversational CRM interactions
"""
from google import genai
from django.conf import settings
from typing import Dict, Any, List, Optional
import json
from . import ai_tools


class AgentService:
    """
    AI Agent that can understand natural language queries and execute CRM actions.
    Uses Gemini's function calling to interact with the CRM system.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI Agent with Gemini function calling support.

        Args:
            api_key: Optional Gemini API key (uses settings if not provided)
        """
        self.api_key = api_key or getattr(settings, 'GEMINI_API_KEY', 'AIzaSyDh5utXAp2887iHPCaAzyJ0JHAfxZPJTeA')
        self.client = genai.Client(api_key=self.api_key)

        # Initialize model with function calling support (Gemini 2.5)
        self.model_name = 'gemini-2.5-flash'
        self.tools = list(ai_tools.AVAILABLE_TOOLS.values())

        # System instruction for the agent
        self.system_instruction = """
You are an AI assistant for MoldCRM, a customer relationship management system.
You help users manage their leads, contacts, and deals through natural conversation.

When a user asks you to perform actions:
1. Use the available tools to access or modify CRM data
2. Always verify you have the necessary information before calling tools
3. Provide clear, concise responses in natural language
4. If you encounter errors, explain them clearly to the user
5. Be proactive - suggest next steps when appropriate

Available capabilities:
- Search and retrieve lead, contact, and deal information
- Create new leads and deals
- Update lead statuses and deal stages
- Generate pipeline and sales reports
- Answer questions about CRM data

Always maintain a professional, helpful tone.
"""

    def process_query(self, query: str, account_id: int, user_id: int,
                     conversation_history: Optional[List] = None) -> Dict[str, Any]:
        """
        Process a user query with multi-turn conversation and function calling.

        Args:
            query: The user's natural language query
            account_id: User's account ID for permission checks
            user_id: User ID for creating records
            conversation_history: Optional list of previous messages in this conversation

        Returns:
            Dictionary containing the agent's response and execution details
        """
        try:
            # Create chat configuration with function calling support
            chat_config = {
                'model': self.model_name,
                'tools': self.tools,
                'system_instruction': self.system_instruction
            }

            # Initialize chat with history if provided
            if conversation_history:
                chat_config['history'] = conversation_history

            # Create chat session and send query
            chat = self.client.chats.create(**chat_config)
            response = chat.send_message(query)

            # Track function calls made
            function_calls_made = []
            max_iterations = 5  # Prevent infinite loops
            iteration = 0

            # Multi-turn execution loop
            while iteration < max_iterations:
                # Check if model wants to call a function
                if response.candidates[0].content.parts:
                    part = response.candidates[0].content.parts[0]

                    # Check for function call
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                        function_name = function_call.name
                        function_args = dict(function_call.args)

                        # Add account_id and user_id to function arguments
                        function_args['account_id'] = account_id
                        if function_name in ['create_lead', 'create_deal']:
                            function_args['user_id'] = user_id

                        # Execute the function
                        tool_function = ai_tools.get_tool_by_name(function_name)
                        if tool_function:
                            function_result = tool_function(**function_args)

                            # Track the call
                            function_calls_made.append({
                                'function': function_name,
                                'arguments': function_args,
                                'result': function_result
                            })

                            # Send the function result back to the model
                            function_response_content = {
                                'parts': [{
                                    'function_response': {
                                        'name': function_name,
                                        'response': {'result': function_result}
                                    }
                                }]
                            }
                            response = chat.send_message(function_response_content)
                            iteration += 1
                            continue
                        else:
                            # Function not found
                            return {
                                'success': False,
                                'response': f"Error: Function '{function_name}' not available",
                                'function_calls': function_calls_made
                            }

                # No more function calls - return the final text response
                final_text = response.text if hasattr(response, 'text') else "I processed your request."

                return {
                    'success': True,
                    'response': final_text,
                    'function_calls': function_calls_made,
                    'conversation_history': chat.history
                }

            # Max iterations reached
            return {
                'success': False,
                'response': "I encountered too many steps processing your request. Please try rephrasing.",
                'function_calls': function_calls_made
            }

        except Exception as e:
            return {
                'success': False,
                'response': f"I encountered an error: {str(e)}",
                'error': str(e)
            }

    def generate_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """
        Generate contextual suggestions for what the user might want to do next.

        Args:
            context: Context information (recent actions, current view, etc.)

        Returns:
            List of suggested queries the user might want to make
        """
        try:
            prompt = f"""
Based on this CRM context, suggest 3 helpful actions the user might want to take next:

Context: {json.dumps(context, indent=2)}

Provide 3 short, actionable suggestions (e.g., "Show me my pipeline summary", "Create a new lead").
Return as a JSON array of strings.
"""
            # Use simple generation for suggestions (no function calling needed)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            # Parse suggestions
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()

            suggestions = json.loads(text)
            return suggestions if isinstance(suggestions, list) else []

        except Exception as e:
            # Return default suggestions on error
            return [
                "Show me my pipeline summary",
                "What are my newest leads?",
                "Create a new lead"
            ]
