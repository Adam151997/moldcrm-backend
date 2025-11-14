"""
Webhook endpoint views for email providers
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
import json
import logging

from integrations.services.adapters.sendgrid_adapter import SendGridAdapter
from integrations.services.adapters.mailgun_adapter import MailgunAdapter
from integrations.services.adapters.brevo_adapter import BrevoAdapter
from integrations.services.adapters.mailchimp_adapter import MailchimpAdapter
from integrations.services.adapters.klaviyo_adapter import KlaviyoAdapter
from .handlers import EmailWebhookHandler

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SendGridWebhookView(APIView):
    """
    Handle SendGrid webhook events
    """
    permission_classes = []  # No authentication required for webhooks
    authentication_classes = []

    def post(self, request):
        try:
            # SendGrid sends events as JSON array
            events = request.data

            if not isinstance(events, list):
                events = [events]

            # Parse events using SendGrid adapter
            adapter = SendGridAdapter('', config={})  # No API key needed for webhook parsing

            parsed_events = []
            for event in events:
                parsed_event = adapter.parse_webhook_event(event)
                if parsed_event:
                    parsed_events.append(parsed_event)

            # Process events
            result = EmailWebhookHandler.process_bulk_events('sendgrid', parsed_events)

            logger.info(f"SendGrid webhook processed: {result}")

            return Response({'status': 'success', 'result': result}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"SendGrid webhook error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class MailgunWebhookView(APIView):
    """
    Handle Mailgun webhook events
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        try:
            # Mailgun sends events as form data
            event_data = request.data

            # Parse event using Mailgun adapter
            adapter = MailgunAdapter('', config={'domain': 'example.com'})
            parsed_event = adapter.parse_webhook_event(event_data)

            if not parsed_event:
                return Response({'error': 'Invalid event data'}, status=status.HTTP_400_BAD_REQUEST)

            # Process event
            success = EmailWebhookHandler.handle_event('mailgun', parsed_event)

            if success:
                logger.info(f"Mailgun webhook processed: {parsed_event.get('event')}")
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to process event'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Mailgun webhook error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class BrevoWebhookView(APIView):
    """
    Handle Brevo (Sendinblue) webhook events
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        try:
            event_data = request.data

            # Parse event using Brevo adapter
            adapter = BrevoAdapter('', config={})
            parsed_event = adapter.parse_webhook_event(event_data)

            if not parsed_event:
                return Response({'error': 'Invalid event data'}, status=status.HTTP_400_BAD_REQUEST)

            # Process event
            success = EmailWebhookHandler.handle_event('brevo', parsed_event)

            if success:
                logger.info(f"Brevo webhook processed: {parsed_event.get('event')}")
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to process event'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Brevo webhook error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class MailchimpWebhookView(APIView):
    """
    Handle Mailchimp (Mandrill) webhook events
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        try:
            # Mandrill sends events in 'mandrill_events' parameter
            event_data = request.data

            # Parse events using Mailchimp adapter
            adapter = MailchimpAdapter('', config={})
            parsed_event = adapter.parse_webhook_event(event_data)

            if not parsed_event:
                return Response({'error': 'Invalid event data'}, status=status.HTTP_400_BAD_REQUEST)

            # Process event
            success = EmailWebhookHandler.handle_event('mailchimp', parsed_event)

            if success:
                logger.info(f"Mailchimp webhook processed: {parsed_event.get('event')}")
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to process event'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Mailchimp webhook error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class KlaviyoWebhookView(APIView):
    """
    Handle Klaviyo webhook events
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        try:
            event_data = request.data

            # Parse event using Klaviyo adapter
            adapter = KlaviyoAdapter('', config={})
            parsed_event = adapter.parse_webhook_event(event_data)

            if not parsed_event:
                return Response({'error': 'Invalid event data'}, status=status.HTTP_400_BAD_REQUEST)

            # Process event
            success = EmailWebhookHandler.handle_event('klaviyo', parsed_event)

            if success:
                logger.info(f"Klaviyo webhook processed: {parsed_event.get('event')}")
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to process event'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Klaviyo webhook error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
