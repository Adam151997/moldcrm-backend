"""
Webhook views for plugin platforms
Handles incoming webhooks from Google Ads, Meta Ads, TikTok Ads, and Shopify
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def google_ads_webhook(request, plugin_id):
    """
    Handle Google Ads webhook events
    Note: Google Ads typically uses Pub/Sub for notifications
    """
    from integrations.models import Plugin
    from integrations.plugins.plugin_service import PluginService

    try:
        plugin = Plugin.objects.get(id=plugin_id, plugin_type='google_ads')

        if request.method == 'GET':
            # Verification request
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)

        # Parse webhook payload
        if request.content_type == 'application/json':
            payload = request.data
        else:
            payload = json.loads(request.body.decode('utf-8'))

        headers = dict(request.headers)

        # Process webhook
        PluginService.process_webhook(plugin, payload, headers)

        return Response({'status': 'received'}, status=status.HTTP_200_OK)

    except Plugin.DoesNotExist:
        return Response({'error': 'Plugin not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def meta_ads_webhook(request, plugin_id):
    """
    Handle Meta Ads (Facebook) webhook events
    Supports verification challenge and event processing
    """
    from integrations.models import Plugin
    from integrations.plugins.plugin_service import PluginService

    try:
        plugin = Plugin.objects.get(id=plugin_id, plugin_type='meta_ads')

        # Handle verification challenge
        if request.method == 'GET':
            verify_token = plugin.webhook_secret or 'default_verify_token'
            mode = request.GET.get('hub.mode')
            token = request.GET.get('hub.verify_token')
            challenge = request.GET.get('hub.challenge')

            if mode == 'subscribe' and token == verify_token:
                return HttpResponse(challenge, content_type='text/plain')
            else:
                return Response({'error': 'Verification failed'}, status=status.HTTP_403_FORBIDDEN)

        # Parse webhook payload
        if request.content_type == 'application/json':
            payload = request.data
        else:
            payload = json.loads(request.body.decode('utf-8'))

        headers = dict(request.headers)

        # Process webhook
        PluginService.process_webhook(plugin, payload, headers)

        return Response({'status': 'received'}, status=status.HTTP_200_OK)

    except Plugin.DoesNotExist:
        return Response({'error': 'Plugin not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def tiktok_ads_webhook(request, plugin_id):
    """
    Handle TikTok Ads webhook events
    """
    from integrations.models import Plugin
    from integrations.plugins.plugin_service import PluginService

    try:
        plugin = Plugin.objects.get(id=plugin_id, plugin_type='tiktok_ads')

        # Parse webhook payload
        if request.content_type == 'application/json':
            payload = request.data
        else:
            payload = json.loads(request.body.decode('utf-8'))

        headers = dict(request.headers)

        # Process webhook
        PluginService.process_webhook(plugin, payload, headers)

        return Response({'status': 'received'}, status=status.HTTP_200_OK)

    except Plugin.DoesNotExist:
        return Response({'error': 'Plugin not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def shopify_webhook(request, plugin_id):
    """
    Handle Shopify webhook events
    """
    from integrations.models import Plugin
    from integrations.plugins.plugin_service import PluginService

    try:
        plugin = Plugin.objects.get(id=plugin_id, plugin_type='shopify')

        # Parse webhook payload
        if request.content_type == 'application/json':
            payload = request.data
        else:
            payload = json.loads(request.body.decode('utf-8'))

        headers = dict(request.headers)

        # Verify webhook signature
        signature = headers.get('X-Shopify-Hmac-Sha256')
        if signature:
            from integrations.plugins.shopify_adapter import ShopifyAdapter
            adapter = ShopifyAdapter(plugin)
            if not adapter.verify_webhook_signature(request.body, signature):
                return Response({'error': 'Invalid signature'}, status=status.HTTP_403_FORBIDDEN)

        # Process webhook
        PluginService.process_webhook(plugin, payload, headers)

        return Response({'status': 'received'}, status=status.HTTP_200_OK)

    except Plugin.DoesNotExist:
        return Response({'error': 'Plugin not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
