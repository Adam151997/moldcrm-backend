"""
Email AI Service - AI-powered features for email campaigns
Leverages Gemini AI for content optimization, send time prediction, and personalization
"""
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime, timedelta
from django.utils import timezone
from automation.services.gemini_ai import GeminiAIService


class EmailAIService:
    """
    AI-powered email campaign optimization service
    Provides subject line optimization, content improvement, send time optimization, and more
    """

    def __init__(self):
        """Initialize the AI service with Gemini backend"""
        self.ai = GeminiAIService()

    def optimize_subject_line(self, subject: str, campaign_type: str = 'marketing',
                             target_audience: str = '') -> Dict[str, Any]:
        """
        Optimize email subject line for better open rates

        Args:
            subject: Original subject line
            campaign_type: Type of campaign (marketing, transactional, newsletter)
            target_audience: Description of target audience

        Returns:
            Dictionary with optimized subject and score
        """
        prompt = f"""
        Optimize this email subject line for maximum open rates:

        Original Subject: "{subject}"
        Campaign Type: {campaign_type}
        Target Audience: {target_audience or 'General'}

        Provide 5 alternative subject lines that:
        1. Are concise (under 50 characters)
        2. Create urgency or curiosity
        3. Are personalized where possible
        4. Avoid spam trigger words
        5. Are A/B test ready (different approaches)

        Also rate the original subject from 0-100.

        Respond in JSON format:
        {{
            "original_score": <number 0-100>,
            "issues": ["<issue1>", "<issue2>"],
            "alternatives": [
                {{
                    "subject": "<alternative subject>",
                    "score": <number 0-100>,
                    "reason": "<why this works>"
                }}
            ]
        }}
        """

        try:
            response = self.ai.model.generate_content(prompt)
            result = self.ai._parse_json_response(response.text)
            return result
        except Exception as e:
            return {
                'original_score': 50,
                'issues': [str(e)],
                'alternatives': []
            }

    def improve_email_content(self, content: str, goal: str = 'engagement') -> Dict[str, Any]:
        """
        Improve email content for better engagement

        Args:
            content: Original email content
            goal: Campaign goal (engagement, conversion, retention)

        Returns:
            Dictionary with improved content and suggestions
        """
        prompt = f"""
        Analyze and improve this email content for {goal}:

        Original Content:
        {content[:1000]}  # Limit content length

        Provide:
        1. Overall score (0-100)
        2. Specific improvements for readability, engagement, and conversion
        3. Suggested changes
        4. Best practices violations

        Respond in JSON format:
        {{
            "score": <number 0-100>,
            "strengths": ["<strength1>", "<strength2>"],
            "weaknesses": ["<weakness1>", "<weakness2>"],
            "suggestions": [
                {{
                    "type": "<type: structure|tone|cta|personalization>",
                    "suggestion": "<specific suggestion>",
                    "priority": "<high|medium|low>"
                }}
            ],
            "improved_version": "<optional: improved version of key sections>"
        }}
        """

        try:
            response = self.ai.model.generate_content(prompt)
            result = self.ai._parse_json_response(response.text)
            return result
        except Exception as e:
            return {
                'score': 50,
                'strengths': [],
                'weaknesses': [str(e)],
                'suggestions': []
            }

    def generate_personalized_content(self, template: str, recipient_data: Dict[str, Any],
                                     tone: str = 'professional') -> str:
        """
        Generate personalized email content using AI

        Args:
            template: Base template or outline
            recipient_data: Information about recipient
            tone: Desired tone (professional, casual, friendly, formal)

        Returns:
            Personalized email content
        """
        prompt = f"""
        Personalize this email template for the recipient:

        Template/Outline:
        {template}

        Recipient Information:
        - Name: {recipient_data.get('first_name', '')} {recipient_data.get('last_name', '')}
        - Company: {recipient_data.get('company', 'their company')}
        - Title: {recipient_data.get('title', '')}
        - Industry: {recipient_data.get('industry', '')}
        - Previous Interactions: {recipient_data.get('interactions', 'None')}

        Tone: {tone}

        Create a personalized version that:
        1. Uses their name and company naturally
        2. References relevant details
        3. Feels genuine, not templated
        4. Maintains the core message

        Return only the personalized email content (no explanations).
        """

        try:
            response = self.ai.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return template  # Fallback to original template

    def predict_optimal_send_time(self, recipient_history: List[Dict[str, Any]],
                                  campaign_type: str = 'marketing') -> Dict[str, Any]:
        """
        Predict optimal send time based on recipient engagement history

        Args:
            recipient_history: List of past email engagements with timestamps
            campaign_type: Type of campaign

        Returns:
            Dictionary with recommended send time and reasoning
        """
        # Analyze historical engagement patterns
        engagement_by_hour = {}
        engagement_by_day = {}

        for engagement in recipient_history:
            if engagement.get('opened_at'):
                dt = datetime.fromisoformat(str(engagement['opened_at']))
                hour = dt.hour
                day = dt.strftime('%A')

                engagement_by_hour[hour] = engagement_by_hour.get(hour, 0) + 1
                engagement_by_day[day] = engagement_by_day.get(day, 0) + 1

        # Use AI to recommend optimal time
        prompt = f"""
        Based on this recipient's email engagement history, recommend the optimal send time:

        Engagement by Hour: {json.dumps(engagement_by_hour)}
        Engagement by Day: {json.dumps(engagement_by_day)}
        Campaign Type: {campaign_type}

        Consider:
        1. Historical patterns
        2. Industry best practices
        3. Campaign type
        4. Time zones (assume EST)

        Respond in JSON format:
        {{
            "recommended_day": "<day of week>",
            "recommended_hour": <hour 0-23>,
            "confidence": <number 0-100>,
            "reasoning": "<brief explanation>",
            "alternative_times": [
                {{"day": "<day>", "hour": <hour>, "score": <number>}}
            ]
        }}
        """

        try:
            response = self.ai.model.generate_content(prompt)
            result = self.ai._parse_json_response(response.text)
            return result
        except Exception as e:
            # Default to industry best practices
            return {
                'recommended_day': 'Tuesday',
                'recommended_hour': 10,
                'confidence': 50,
                'reasoning': f'Using default best practice (error: {str(e)})',
                'alternative_times': []
            }

    def generate_ab_test_variants(self, element: str, content: str,
                                  num_variants: int = 3) -> List[Dict[str, Any]]:
        """
        Generate A/B test variants for email elements

        Args:
            element: Element to test (subject, cta, header, body)
            content: Original content
            num_variants: Number of variants to generate

        Returns:
            List of variant dictionaries
        """
        prompt = f"""
        Generate {num_variants} A/B test variants for this email {element}:

        Original: "{content}"

        Create variants that test different approaches:
        - Different messaging angles
        - Different tones
        - Different value propositions
        - Different urgency levels

        Respond in JSON format:
        [
            {{
                "variant_name": "<descriptive name>",
                "content": "<variant content>",
                "hypothesis": "<what this tests>",
                "expected_winner": "<why this might win>"
            }}
        ]
        """

        try:
            response = self.ai.model.generate_content(prompt)
            result = self.ai._parse_json_response(response.text)
            if isinstance(result, list):
                return result[:num_variants]
            return []
        except Exception as e:
            return []

    def analyze_campaign_performance(self, campaign_stats: Dict[str, Any],
                                    industry_benchmarks: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Analyze campaign performance and provide insights

        Args:
            campaign_stats: Campaign performance metrics
            industry_benchmarks: Optional industry benchmark data

        Returns:
            Dictionary with analysis and recommendations
        """
        benchmarks = industry_benchmarks or {
            'open_rate': 21.5,
            'click_rate': 2.6,
            'conversion_rate': 1.2,
            'unsubscribe_rate': 0.1
        }

        prompt = f"""
        Analyze this email campaign performance:

        Campaign Stats:
        - Sent: {campaign_stats.get('sent_count', 0)}
        - Opens: {campaign_stats.get('opens_count', 0)} ({campaign_stats.get('open_rate', 0):.1f}%)
        - Clicks: {campaign_stats.get('clicks_count', 0)} ({campaign_stats.get('click_rate', 0):.1f}%)
        - Conversions: {campaign_stats.get('conversions', 0)} ({campaign_stats.get('conversion_rate', 0):.1f}%)
        - Bounces: {campaign_stats.get('bounces', 0)} ({campaign_stats.get('bounce_rate', 0):.1f}%)
        - Unsubscribes: {campaign_stats.get('unsubscribes', 0)} ({campaign_stats.get('unsubscribe_rate', 0):.1f}%)

        Industry Benchmarks:
        - Open Rate: {benchmarks['open_rate']:.1f}%
        - Click Rate: {benchmarks['click_rate']:.1f}%
        - Conversion Rate: {benchmarks['conversion_rate']:.1f}%
        - Unsubscribe Rate: {benchmarks['unsubscribe_rate']:.1f}%

        Provide:
        1. Overall performance rating (excellent/good/average/poor)
        2. Key strengths and weaknesses
        3. Specific actionable recommendations
        4. Predicted improvements if recommendations are followed

        Respond in JSON format:
        {{
            "rating": "<rating>",
            "overall_score": <number 0-100>,
            "strengths": ["<strength1>", "<strength2>"],
            "weaknesses": ["<weakness1>", "<weakness2>"],
            "recommendations": [
                {{
                    "area": "<area to improve>",
                    "action": "<specific action>",
                    "expected_impact": "<impact description>",
                    "priority": "<high|medium|low>"
                }}
            ],
            "key_insight": "<most important takeaway>"
        }}
        """

        try:
            response = self.ai.model.generate_content(prompt)
            result = self.ai._parse_json_response(response.text)
            return result
        except Exception as e:
            return {
                'rating': 'unknown',
                'overall_score': 50,
                'strengths': [],
                'weaknesses': [str(e)],
                'recommendations': []
            }

    def suggest_segment_criteria(self, campaign_goal: str,
                                existing_segments: List[str] = None) -> Dict[str, Any]:
        """
        Suggest segment criteria for better targeting

        Args:
            campaign_goal: Goal of the campaign
            existing_segments: List of existing segment names

        Returns:
            Dictionary with suggested segments
        """
        prompt = f"""
        Suggest effective audience segments for this campaign goal:

        Campaign Goal: {campaign_goal}
        Existing Segments: {', '.join(existing_segments) if existing_segments else 'None'}

        Suggest 3-5 new segment ideas that would improve targeting:
        1. Based on behavior (engagement, purchase history)
        2. Based on demographics
        3. Based on lifecycle stage

        Respond in JSON format:
        {{
            "segments": [
                {{
                    "name": "<segment name>",
                    "description": "<what defines this segment>",
                    "criteria": [
                        {{"field": "<field>", "operator": "<operator>", "value": "<value>"}}
                    ],
                    "estimated_size": "<small|medium|large>",
                    "expected_performance": "<why this segment would perform well>"
                }}
            ]
        }}
        """

        try:
            response = self.ai.model.generate_content(prompt)
            result = self.ai._parse_json_response(response.text)
            return result
        except Exception as e:
            return {'segments': []}

    def generate_drip_sequence(self, goal: str, duration_days: int = 14,
                              target_audience: str = '') -> Dict[str, Any]:
        """
        Generate a drip campaign sequence

        Args:
            goal: Goal of drip campaign
            duration_days: Total duration in days
            target_audience: Description of audience

        Returns:
            Dictionary with drip sequence steps
        """
        prompt = f"""
        Create a drip email sequence for this goal:

        Goal: {goal}
        Duration: {duration_days} days
        Target Audience: {target_audience or 'General'}

        Design a sequence that:
        1. Gradually builds relationship
        2. Provides value at each step
        3. Has clear progression toward goal
        4. Includes appropriate delays between emails

        Respond in JSON format:
        {{
            "sequence_name": "<descriptive name>",
            "total_steps": <number>,
            "steps": [
                {{
                    "step_number": <number>,
                    "delay_days": <days after previous email>,
                    "subject": "<subject line>",
                    "purpose": "<what this email achieves>",
                    "key_content": "<main message/value>",
                    "call_to_action": "<primary CTA>",
                    "notes": "<implementation notes>"
                }}
            ]
        }}
        """

        try:
            response = self.ai.model.generate_content(prompt)
            result = self.ai._parse_json_response(response.text)
            return result
        except Exception as e:
            return {
                'sequence_name': 'Default Sequence',
                'total_steps': 0,
                'steps': []
            }

    def predict_unsubscribe_risk(self, recipient_data: Dict[str, Any],
                                campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict if recipient is at risk of unsubscribing

        Args:
            recipient_data: Recipient engagement history
            campaign_data: Planned campaign details

        Returns:
            Dictionary with risk assessment
        """
        prompt = f"""
        Assess unsubscribe risk for this recipient:

        Recipient History:
        - Total Emails Received: {recipient_data.get('emails_received', 0)}
        - Recent Open Rate: {recipient_data.get('recent_open_rate', 0):.1f}%
        - Recent Click Rate: {recipient_data.get('recent_click_rate', 0):.1f}%
        - Days Since Last Open: {recipient_data.get('days_since_last_open', 0)}
        - Days Since Last Click: {recipient_data.get('days_since_last_click', 0)}
        - Previous Unsubscribe Attempts: {recipient_data.get('unsubscribe_attempts', 0)}

        Planned Campaign:
        - Type: {campaign_data.get('type', 'marketing')}
        - Frequency: {campaign_data.get('frequency', 'weekly')}

        Assess risk level and provide recommendations.

        Respond in JSON format:
        {{
            "risk_level": "<low|medium|high>",
            "risk_score": <number 0-100>,
            "factors": ["<factor1>", "<factor2>"],
            "recommendations": ["<recommendation1>", "<recommendation2>"],
            "should_send": <boolean>
        }}
        """

        try:
            response = self.ai.model.generate_content(prompt)
            result = self.ai._parse_json_response(response.text)
            return result
        except Exception as e:
            return {
                'risk_level': 'medium',
                'risk_score': 50,
                'factors': [str(e)],
                'recommendations': [],
                'should_send': True
            }

    def calculate_engagement_score(self, email_history: List[Dict[str, Any]]) -> int:
        """
        Calculate engagement score for a contact based on email history

        Args:
            email_history: List of email engagement records

        Returns:
            Engagement score (0-100)
        """
        if not email_history:
            return 0

        score = 0
        total_emails = len(email_history)

        # Calculate metrics
        opens = sum(1 for e in email_history if e.get('opened'))
        clicks = sum(1 for e in email_history if e.get('clicked'))
        recent_engagement = sum(1 for e in email_history[:5] if e.get('opened'))  # Last 5 emails

        # Scoring algorithm
        open_rate = (opens / total_emails) * 100 if total_emails > 0 else 0
        click_rate = (clicks / total_emails) * 100 if total_emails > 0 else 0
        recent_rate = (recent_engagement / min(5, total_emails)) * 100 if total_emails > 0 else 0

        # Weighted score
        score = (
            open_rate * 0.4 +  # 40% weight on opens
            click_rate * 0.4 +  # 40% weight on clicks
            recent_rate * 0.2   # 20% weight on recent activity
        )

        return int(min(score, 100))
