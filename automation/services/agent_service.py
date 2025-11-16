"""
AI Agent Service - Handles multi-turn conversations with function calling
Uses Gemini 2.5 Flash with function calling to enable conversational CRM interactions
"""
from google import genai
from google.genai import types
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
        self.tools = self._create_function_declarations()

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

    def _create_function_declarations(self):
        """
        Create function declarations for the Gemini API.
        Note: Default values are NOT included as they're not supported by Gemini API.
        """
        function_declarations = [
            types.FunctionDeclaration(
                name='get_lead',
                description='Retrieve detailed information about a specific lead',
                parameters={
                    'type': 'object',
                    'properties': {
                        'lead_id': {'type': 'integer', 'description': 'The unique identifier of the lead'},
                    },
                    'required': ['lead_id']
                }
            ),
            types.FunctionDeclaration(
                name='get_deal',
                description='Retrieve detailed information about a specific deal',
                parameters={
                    'type': 'object',
                    'properties': {
                        'deal_id': {'type': 'integer', 'description': 'The unique identifier of the deal'},
                    },
                    'required': ['deal_id']
                }
            ),
            types.FunctionDeclaration(
                name='get_contact',
                description='Retrieve detailed information about a specific contact',
                parameters={
                    'type': 'object',
                    'properties': {
                        'contact_id': {'type': 'integer', 'description': 'The unique identifier of the contact'},
                    },
                    'required': ['contact_id']
                }
            ),
            types.FunctionDeclaration(
                name='create_lead',
                description='Create a new lead in the CRM system',
                parameters={
                    'type': 'object',
                    'properties': {
                        'first_name': {'type': 'string', 'description': "Lead's first name"},
                        'last_name': {'type': 'string', 'description': "Lead's last name"},
                        'email': {'type': 'string', 'description': "Lead's email address"},
                        'company': {'type': 'string', 'description': "Lead's company name (optional)"},
                        'phone': {'type': 'string', 'description': "Lead's phone number (optional)"},
                        'source': {'type': 'string', 'description': 'How the lead was acquired (optional)'},
                        'notes': {'type': 'string', 'description': 'Additional notes about the lead (optional)'},
                    },
                    'required': ['first_name', 'last_name', 'email']
                }
            ),
            types.FunctionDeclaration(
                name='create_deal',
                description='Create a new deal in the CRM system',
                parameters={
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string', 'description': 'Deal name/title'},
                        'contact_id': {'type': 'integer', 'description': 'ID of the contact associated with this deal'},
                        'amount': {'type': 'number', 'description': 'Deal amount in dollars (optional)'},
                        'probability': {'type': 'integer', 'description': 'Probability of closing 0-100 (optional)'},
                        'expected_close_date': {'type': 'string', 'description': 'Expected close date in ISO format YYYY-MM-DD (optional)'},
                        'notes': {'type': 'string', 'description': 'Additional notes about the deal (optional)'},
                    },
                    'required': ['name', 'contact_id']
                }
            ),
            types.FunctionDeclaration(
                name='update_lead_status',
                description='Update the status of an existing lead',
                parameters={
                    'type': 'object',
                    'properties': {
                        'lead_id': {'type': 'integer', 'description': 'The unique identifier of the lead to update'},
                        'new_status': {'type': 'string', 'description': "New status value (must be one of: 'new', 'contacted', 'qualified', 'unqualified')"},
                    },
                    'required': ['lead_id', 'new_status']
                }
            ),
            types.FunctionDeclaration(
                name='update_deal_stage',
                description='Update the stage of an existing deal',
                parameters={
                    'type': 'object',
                    'properties': {
                        'deal_id': {'type': 'integer', 'description': 'The unique identifier of the deal to update'},
                        'new_stage': {'type': 'string', 'description': "New stage value (must be one of: 'prospect', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost')"},
                    },
                    'required': ['deal_id', 'new_stage']
                }
            ),
            types.FunctionDeclaration(
                name='get_pipeline_summary',
                description='Get a comprehensive summary of the sales pipeline including deal counts and values by stage',
                parameters={
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            ),
            types.FunctionDeclaration(
                name='get_leads_summary',
                description='Get a summary of leads with optional filtering by status',
                parameters={
                    'type': 'object',
                    'properties': {
                        'status_filter': {'type': 'string', 'description': "Optional status to filter by ('new', 'contacted', 'qualified', 'unqualified')"},
                    },
                    'required': []
                }
            ),
            types.FunctionDeclaration(
                name='search_leads',
                description='Search for leads by name, email, or company',
                parameters={
                    'type': 'object',
                    'properties': {
                        'query': {'type': 'string', 'description': 'Search query string'},
                        'limit': {'type': 'integer', 'description': 'Maximum number of results to return'},
                    },
                    'required': ['query']
                }
            ),
            types.FunctionDeclaration(
                name='search_deals',
                description='Search for deals by name or contact information',
                parameters={
                    'type': 'object',
                    'properties': {
                        'query': {'type': 'string', 'description': 'Search query string'},
                        'limit': {'type': 'integer', 'description': 'Maximum number of results to return'},
                    },
                    'required': ['query']
                }
            ),
        ]

        # Wrap declarations in a Tool
        return [types.Tool(function_declarations=function_declarations)]

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
            # Disable automatic function calling since we need to inject account_id/user_id
            config = types.GenerateContentConfig(
                tools=self.tools,
                system_instruction=self.system_instruction,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )

            # Create chat session with tools and system instruction
            # Pass conversation history if provided to maintain context
            chat_params = {
                'model': self.model_name,
                'config': config
            }
            if conversation_history:
                chat_params['history'] = conversation_history

            chat = self.client.chats.create(**chat_params)

            # Send the user's query
            response = chat.send_message(query)

            # Track function calls made
            function_calls_made = []
            max_iterations = 5  # Prevent infinite loops
            iteration = 0

            # Multi-turn execution loop
            while iteration < max_iterations:
                # Check if model wants to call a function
                if response.function_calls:
                    # Get the first function call
                    function_call = response.function_calls[0]
                    function_name = function_call.name
                    function_args = dict(function_call.args)

                    # Add account_id and user_id to function arguments
                    function_args['account_id'] = account_id
                    if function_name in ['create_lead', 'create_deal']:
                        function_args['user_id'] = user_id

                    # Execute the function
                    tool_function = ai_tools.get_tool_by_name(function_name)
                    if tool_function:
                        try:
                            function_result = tool_function(**function_args)
                        except Exception as func_error:
                            # If function execution fails, return error to user
                            return {
                                'success': False,
                                'response': f"Error executing {function_name}: {str(func_error)}",
                                'error': str(func_error),
                                'function_calls': function_calls_made
                            }

                        # Track the call
                        function_calls_made.append({
                            'function': function_name,
                            'arguments': function_args,
                            'result': function_result
                        })

                        # Send the function result back to the model
                        try:
                            function_response_part = types.Part.from_function_response(
                                name=function_name,
                                response={'result': function_result}
                            )
                            response = chat.send_message(function_response_part)
                        except Exception as send_error:
                            # If sending function response fails, return error
                            return {
                                'success': False,
                                'response': f"Error sending function response: {str(send_error)}",
                                'error': str(send_error),
                                'function_calls': function_calls_made
                            }

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
                    'function_calls': function_calls_made
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
