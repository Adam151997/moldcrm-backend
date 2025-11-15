"""
Template Engine Service - Advanced email template rendering
Supports variables, conditionals, loops, filters, and personalization
"""
import re
from typing import Dict, Any, Optional
from datetime import datetime
from django.template import Template, Context
from django.utils.html import escape
from django.conf import settings


class TemplateEngine:
    """
    Advanced template rendering engine for email campaigns
    Supports Django template syntax plus custom email-specific features
    """

    # Custom filters for email templates
    CUSTOM_FILTERS = {
        'capitalize_each': lambda text: ' '.join(word.capitalize() for word in str(text).split()),
        'currency': lambda amount: f"${float(amount):,.2f}",
        'percentage': lambda value: f"{float(value):.1f}%",
        'short_date': lambda date: date.strftime('%b %d, %Y') if isinstance(date, datetime) else date,
        'relative_date': lambda date: _get_relative_date(date),
    }

    def __init__(self):
        """Initialize the template engine"""
        self.tracking_enabled = True
        self.utm_params = {}

    def render(self, template_content: str, context_data: Dict[str, Any],
               recipient: Optional[Any] = None, campaign: Optional[Any] = None) -> str:
        """
        Render email template with context data

        Args:
            template_content: HTML template string with template variables
            context_data: Dictionary of variables to inject
            recipient: Contact or Lead instance
            campaign: EmailCampaign instance

        Returns:
            Rendered HTML string
        """
        # Build complete context
        full_context = self._build_context(context_data, recipient, campaign)

        # Apply custom filters
        processed_content = self._apply_custom_filters(template_content)

        # Render Django template
        template = Template(processed_content)
        context = Context(full_context)
        rendered = template.render(context)

        # Add tracking pixels and links if enabled
        if self.tracking_enabled and recipient and campaign:
            rendered = self._add_tracking(rendered, recipient, campaign)

        # Add UTM parameters to links
        if self.utm_params:
            rendered = self._add_utm_parameters(rendered, self.utm_params)

        return rendered

    def _build_context(self, context_data: Dict[str, Any],
                      recipient: Optional[Any] = None,
                      campaign: Optional[Any] = None) -> Dict[str, Any]:
        """
        Build complete template context with recipient and campaign data

        Args:
            context_data: Custom context variables
            recipient: Contact or Lead instance
            campaign: EmailCampaign instance

        Returns:
            Complete context dictionary
        """
        context = {
            'today': datetime.now(),
            'current_year': datetime.now().year,
            **context_data
        }

        # Add recipient data
        if recipient:
            context['recipient'] = {
                'first_name': getattr(recipient, 'first_name', ''),
                'last_name': getattr(recipient, 'last_name', ''),
                'email': getattr(recipient, 'email', ''),
                'full_name': getattr(recipient, 'get_full_name', lambda: '')(),
                'company': getattr(recipient, 'company', ''),
                'title': getattr(recipient, 'title', ''),
                'phone': getattr(recipient, 'phone', ''),
            }

            # Add custom fields if available
            if hasattr(recipient, 'custom_fields') and recipient.custom_fields:
                context['recipient']['custom'] = recipient.custom_fields

        # Add campaign data
        if campaign:
            context['campaign'] = {
                'name': campaign.name,
                'subject': campaign.subject,
                'from_name': campaign.from_name,
                'from_email': campaign.from_email,
            }

            # Add unsubscribe link
            if recipient:
                context['unsubscribe_url'] = self._generate_unsubscribe_url(campaign, recipient)

        return context

    def _apply_custom_filters(self, content: str) -> str:
        """
        Apply custom email-specific filters to template

        Args:
            content: Template content

        Returns:
            Processed content with custom filters applied
        """
        # Replace custom filter syntax: {{variable|filter_name}}
        # This is a preprocessing step before Django template rendering

        # Note: Django templates already support filters, but we can add custom ones here
        # For now, we'll rely on Django's built-in filter system
        return content

    def _add_tracking(self, html_content: str, recipient: Any, campaign: Any) -> str:
        """
        Add tracking pixel and convert links to trackable links

        Args:
            html_content: Rendered HTML content
            recipient: Contact or Lead instance
            campaign: EmailCampaign instance

        Returns:
            HTML with tracking enabled
        """
        # Add tracking pixel at the end of the body
        tracking_pixel = self._generate_tracking_pixel(campaign, recipient)
        html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')

        # Convert links to trackable links
        html_content = self._convert_links_to_trackable(html_content, campaign, recipient)

        return html_content

    def _generate_tracking_pixel(self, campaign: Any, recipient: Any) -> str:
        """
        Generate tracking pixel HTML

        Args:
            campaign: EmailCampaign instance
            recipient: Contact or Lead instance

        Returns:
            Tracking pixel HTML
        """
        # Generate unique tracking ID
        tracking_id = f"{campaign.id}-{recipient.id}-{datetime.now().timestamp()}"

        tracking_url = f"{settings.SITE_URL}/api/webhooks/email/track-open/{campaign.id}/{recipient.id}/"

        return f'<img src="{tracking_url}" width="1" height="1" alt="" style="display:none;" />'

    def _convert_links_to_trackable(self, html_content: str, campaign: Any, recipient: Any) -> str:
        """
        Convert all links in email to trackable links

        Args:
            html_content: HTML content
            campaign: EmailCampaign instance
            recipient: Contact or Lead instance

        Returns:
            HTML with trackable links
        """
        # Find all <a> tags with href
        link_pattern = r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"'

        def replace_link(match):
            original_url = match.group(1)

            # Skip if it's an unsubscribe link or already a tracking link
            if 'unsubscribe' in original_url or 'track-click' in original_url:
                return match.group(0)

            # Generate tracking URL
            tracking_url = self._generate_click_tracking_url(campaign, recipient, original_url)

            return match.group(0).replace(original_url, tracking_url)

        return re.sub(link_pattern, replace_link, html_content)

    def _generate_click_tracking_url(self, campaign: Any, recipient: Any, original_url: str) -> str:
        """
        Generate click tracking URL

        Args:
            campaign: EmailCampaign instance
            recipient: Contact or Lead instance
            original_url: Original destination URL

        Returns:
            Tracking URL that redirects to original
        """
        import urllib.parse

        encoded_url = urllib.parse.quote(original_url, safe='')
        tracking_url = f"{settings.SITE_URL}/api/webhooks/email/track-click/{campaign.id}/{recipient.id}/?url={encoded_url}"

        return tracking_url

    def _add_utm_parameters(self, html_content: str, utm_params: Dict[str, str]) -> str:
        """
        Add UTM parameters to all links

        Args:
            html_content: HTML content
            utm_params: Dictionary of UTM parameters

        Returns:
            HTML with UTM parameters added
        """
        import urllib.parse

        link_pattern = r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"'

        def add_utm_to_link(match):
            original_url = match.group(1)

            # Skip internal links and mailto links
            if original_url.startswith('#') or original_url.startswith('mailto:'):
                return match.group(0)

            # Parse URL
            parsed = urllib.parse.urlparse(original_url)
            query_params = urllib.parse.parse_qs(parsed.query)

            # Add UTM parameters
            for key, value in utm_params.items():
                if key.startswith('utm_'):
                    query_params[key] = [value]

            # Rebuild URL
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            new_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))

            return match.group(0).replace(original_url, new_url)

        return re.sub(link_pattern, add_utm_to_link, html_content)

    def _generate_unsubscribe_url(self, campaign: Any, recipient: Any) -> str:
        """
        Generate unsubscribe URL for recipient

        Args:
            campaign: EmailCampaign instance
            recipient: Contact or Lead instance

        Returns:
            Unsubscribe URL
        """
        return f"{settings.SITE_URL}/unsubscribe/{campaign.id}/{recipient.id}/"

    def validate_template(self, template_content: str) -> tuple[bool, Optional[str]]:
        """
        Validate template syntax

        Args:
            template_content: Template content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            Template(template_content)
            return True, None
        except Exception as e:
            return False, str(e)

    def extract_variables(self, template_content: str) -> list:
        """
        Extract all variables used in template

        Args:
            template_content: Template content

        Returns:
            List of variable names
        """
        # Find all Django template variables: {{ variable }}
        variable_pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*(?:\|[^}]*)?\}\}'
        variables = re.findall(variable_pattern, template_content)

        return list(set(variables))

    def preview_with_sample_data(self, template_content: str) -> str:
        """
        Render template with sample data for preview

        Args:
            template_content: Template content

        Returns:
            Rendered preview HTML
        """
        sample_data = {
            'recipient': {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'full_name': 'John Doe',
                'company': 'Acme Corporation',
                'title': 'Marketing Director',
                'phone': '+1 (555) 123-4567',
            },
            'campaign': {
                'name': 'Sample Campaign',
                'subject': 'Check out our latest offers!',
                'from_name': 'Marketing Team',
                'from_email': 'marketing@example.com',
            },
            'unsubscribe_url': '#unsubscribe',
        }

        # Disable tracking for preview
        original_tracking = self.tracking_enabled
        self.tracking_enabled = False

        rendered = self.render(template_content, sample_data)

        # Restore tracking setting
        self.tracking_enabled = original_tracking

        return rendered

    def calculate_spam_score(self, template_content: str, subject: str) -> float:
        """
        Calculate spam score for template

        Args:
            template_content: HTML template content
            subject: Email subject line

        Returns:
            Spam score (0-100, lower is better)
        """
        score = 0.0

        # Check for spam trigger words
        spam_words = [
            'free', 'win', 'winner', 'cash', 'prize', 'click here', 'act now',
            'limited time', 'urgent', 'guarantee', 'no obligation', 'risk-free'
        ]

        content_lower = template_content.lower() + ' ' + subject.lower()

        for word in spam_words:
            if word in content_lower:
                score += 5.0

        # Check for excessive capitalization in subject
        if subject.isupper() and len(subject) > 10:
            score += 10.0

        # Check for excessive exclamation marks
        exclamation_count = subject.count('!')
        if exclamation_count > 1:
            score += exclamation_count * 5.0

        # Check HTML/text ratio
        text_content = re.sub(r'<[^>]+>', '', template_content)
        if len(text_content) < len(template_content) * 0.1:  # Less than 10% text
            score += 15.0

        # Check for too many links
        link_count = len(re.findall(r'<a\s+(?:[^>]*?\s+)?href=', template_content))
        if link_count > 10:
            score += (link_count - 10) * 2.0

        # Cap at 100
        return min(score, 100.0)


def _get_relative_date(date: datetime) -> str:
    """
    Convert date to relative format (e.g., '2 days ago')

    Args:
        date: DateTime object

    Returns:
        Relative date string
    """
    if not isinstance(date, datetime):
        return str(date)

    now = datetime.now()
    diff = now - date

    if diff.days == 0:
        return 'Today'
    elif diff.days == 1:
        return 'Yesterday'
    elif diff.days < 7:
        return f'{diff.days} days ago'
    elif diff.days < 30:
        weeks = diff.days // 7
        return f'{weeks} week{"s" if weeks > 1 else ""} ago'
    elif diff.days < 365:
        months = diff.days // 30
        return f'{months} month{"s" if months > 1 else ""} ago'
    else:
        years = diff.days // 365
        return f'{years} year{"s" if years > 1 else ""} ago'
