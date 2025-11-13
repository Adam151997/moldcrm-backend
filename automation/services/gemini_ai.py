import google.generativeai as genai
from django.conf import settings
from typing import Dict, Any, Optional, List
import json


class GeminiAIService:
    """
    Service for interacting with Google's Gemini AI API
    API Key: AIzaSyDh5utXAp2887iHPCaAzyJ0JHAfxZPJTeA
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'GEMINI_API_KEY', 'AIzaSyDh5utXAp2887iHPCaAzyJ0JHAfxZPJTeA')
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_lead_score(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a lead based on various factors
        Returns: {'score': 0-100, 'reasoning': str, 'recommendations': []}
        """
        prompt = f"""
        Analyze this lead and provide a score from 0-100 based on their potential value:
        
        Lead Information:
        - Name: {lead_data.get('first_name')} {lead_data.get('last_name')}
        - Company: {lead_data.get('company')}
        - Status: {lead_data.get('status')}
        - Source: {lead_data.get('source')}
        - Notes: {lead_data.get('notes', 'None')}
        
        Provide a JSON response with:
        {{
            "score": <number 0-100>,
            "reasoning": "<brief explanation>",
            "recommendations": ["<action1>", "<action2>"]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            return result
        except Exception as e:
            return {
                'score': 50,
                'reasoning': f'Unable to score lead: {str(e)}',
                'recommendations': ['Manual review recommended']
            }
    
    def predict_deal_outcome(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict likelihood of deal closing
        Returns: {'probability': 0-100, 'predicted_close_date': str, 'insights': []}
        """
        prompt = f"""
        Analyze this deal and predict its outcome:
        
        Deal Information:
        - Name: {deal_data.get('name')}
        - Amount: ${deal_data.get('amount', 0)}
        - Stage: {deal_data.get('stage')}
        - Expected Close: {deal_data.get('expected_close_date', 'Not set')}
        - Probability: {deal_data.get('probability', 0)}%
        - Contact: {deal_data.get('contact_name', 'Unknown')}
        
        Provide a JSON response with:
        {{
            "probability": <number 0-100>,
            "predicted_close_date": "<ISO date or 'uncertain'>",
            "insights": ["<insight1>", "<insight2>"],
            "risk_factors": ["<risk1>", "<risk2>"]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            return result
        except Exception as e:
            return {
                'probability': deal_data.get('probability', 50),
                'predicted_close_date': 'uncertain',
                'insights': [f'Error: {str(e)}'],
                'risk_factors': []
            }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of customer communications
        Returns: {'sentiment': 'positive/neutral/negative', 'confidence': 0-1, 'summary': str}
        """
        prompt = f"""
        Analyze the sentiment of this customer communication:
        
        Text: "{text}"
        
        Provide a JSON response with:
        {{
            "sentiment": "<positive/neutral/negative>",
            "confidence": <number 0-1>,
            "summary": "<brief summary>"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            return result
        except Exception as e:
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'summary': f'Unable to analyze: {str(e)}'
            }
    
    def generate_email_suggestion(self, context: Dict[str, Any]) -> str:
        """
        Generate email content suggestions based on context
        """
        prompt = f"""
        Generate a professional email for this context:
        
        Type: {context.get('email_type', 'follow-up')}
        Recipient: {context.get('recipient_name')}
        Company: {context.get('company', 'their company')}
        Context: {context.get('context', '')}
        Tone: {context.get('tone', 'professional and friendly')}
        
        Write a concise, professional email (subject and body).
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Unable to generate email: {str(e)}"
    
    def generate_deal_summary(self, deal_data: Dict[str, Any], activities: List[Dict]) -> str:
        """
        Generate a summary of deal progress and activities
        """
        activities_text = "\n".join([
            f"- {a.get('activity_type')}: {a.get('title')} ({a.get('created_at')})"
            for a in activities[:10]  # Latest 10 activities
        ])
        
        prompt = f"""
        Summarize this deal's progress:
        
        Deal: {deal_data.get('name')}
        Amount: ${deal_data.get('amount', 0)}
        Stage: {deal_data.get('stage')}
        
        Recent Activities:
        {activities_text or 'No recent activities'}
        
        Provide a concise summary highlighting:
        1. Current status
        2. Key activities
        3. Next steps recommendations
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Unable to generate summary: {str(e)}"
    
    def suggest_next_action(self, lead_or_deal_data: Dict[str, Any]) -> List[str]:
        """
        Suggest next best actions based on current state
        """
        prompt = f"""
        Based on this information, suggest the top 3 next actions:
        
        Data: {json.dumps(lead_or_deal_data, indent=2)}
        
        Provide actionable, specific recommendations as a JSON array:
        ["action1", "action2", "action3"]
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            if isinstance(result, list):
                return result
            return ['Review and update', 'Follow up with contact', 'Update notes']
        except Exception as e:
            return ['Error generating suggestions', 'Manual review recommended']
    
    def _parse_json_response(self, text: str) -> Any:
        """
        Parse JSON from Gemini response, handling markdown code blocks
        """
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
            # If it's a list
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
            raise
