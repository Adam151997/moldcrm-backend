"""
Segmentation Engine Service - Convert visual filters to Django querysets
Handles dynamic and static segments for email campaigns
"""
from typing import Dict, Any, List, Optional
from django.db.models import Q, QuerySet, Count, Sum, Avg, Max, Min, F
from django.utils import timezone
from datetime import datetime, timedelta
from crm.models import Contact, Lead, Deal
from integrations.models import Email, EmailEngagement, LinkClick


class SegmentationEngine:
    """
    Advanced segmentation engine for creating targeted recipient lists
    Supports dynamic filtering, behavioral triggers, and engagement metrics
    """

    # Supported filter operators
    OPERATORS = {
        'equals': lambda field, value: Q(**{field: value}),
        'not_equals': lambda field, value: ~Q(**{field: value}),
        'contains': lambda field, value: Q(**{f'{field}__icontains': value}),
        'not_contains': lambda field, value: ~Q(**{f'{field}__icontains': value}),
        'starts_with': lambda field, value: Q(**{f'{field}__istartswith': value}),
        'ends_with': lambda field, value: Q(**{f'{field}__iendswith': value}),
        'greater_than': lambda field, value: Q(**{f'{field}__gt': value}),
        'greater_than_or_equal': lambda field, value: Q(**{f'{field}__gte': value}),
        'less_than': lambda field, value: Q(**{f'{field}__lt': value}),
        'less_than_or_equal': lambda field, value: Q(**{f'{field}__lte': value}),
        'in': lambda field, value: Q(**{f'{field}__in': value}),
        'not_in': lambda field, value: ~Q(**{f'{field}__in': value}),
        'is_null': lambda field, value: Q(**{f'{field}__isnull': True}),
        'is_not_null': lambda field, value: Q(**{f'{field}__isnull': False}),
        'between': lambda field, value: Q(**{f'{field}__gte': value[0], f'{field}__lte': value[1]}),
    }

    # Date range helpers
    DATE_RANGES = {
        'today': lambda: (timezone.now().replace(hour=0, minute=0, second=0), timezone.now()),
        'yesterday': lambda: (
            timezone.now().replace(hour=0, minute=0, second=0) - timedelta(days=1),
            timezone.now().replace(hour=0, minute=0, second=0)
        ),
        'last_7_days': lambda: (timezone.now() - timedelta(days=7), timezone.now()),
        'last_30_days': lambda: (timezone.now() - timedelta(days=30), timezone.now()),
        'last_90_days': lambda: (timezone.now() - timedelta(days=90), timezone.now()),
        'this_month': lambda: (
            timezone.now().replace(day=1, hour=0, minute=0, second=0),
            timezone.now()
        ),
        'last_month': lambda: _get_last_month_range(),
        'this_year': lambda: (
            timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0),
            timezone.now()
        ),
    }

    def __init__(self, account):
        """
        Initialize segmentation engine for an account

        Args:
            account: Account instance to scope queries
        """
        self.account = account

    def build_queryset(self, filter_conditions: Dict[str, Any],
                      model_type: str = 'contact') -> QuerySet:
        """
        Build Django queryset from filter conditions

        Args:
            filter_conditions: Dictionary defining filter rules
            model_type: 'contact' or 'lead'

        Returns:
            Filtered QuerySet

        Example filter_conditions:
        {
            "match": "all",  # or "any"
            "rules": [
                {
                    "field": "status",
                    "operator": "equals",
                    "value": "active"
                },
                {
                    "field": "created_at",
                    "operator": "greater_than",
                    "value": "2024-01-01"
                }
            ],
            "groups": [
                {
                    "match": "any",
                    "rules": [...]
                }
            ]
        }
        """
        # Get base model
        if model_type == 'contact':
            queryset = Contact.objects.filter(account=self.account)
        elif model_type == 'lead':
            queryset = Lead.objects.filter(account=self.account)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        # Build Q object from conditions
        q_object = self._build_q_object(filter_conditions)

        if q_object:
            queryset = queryset.filter(q_object)

        return queryset.distinct()

    def _build_q_object(self, conditions: Dict[str, Any]) -> Optional[Q]:
        """
        Recursively build Q object from filter conditions

        Args:
            conditions: Filter conditions dictionary

        Returns:
            Q object or None
        """
        if not conditions:
            return None

        match_type = conditions.get('match', 'all')  # 'all' (AND) or 'any' (OR)
        rules = conditions.get('rules', [])
        groups = conditions.get('groups', [])

        q_objects = []

        # Process rules
        for rule in rules:
            q_obj = self._build_rule_q_object(rule)
            if q_obj:
                q_objects.append(q_obj)

        # Process nested groups
        for group in groups:
            q_obj = self._build_q_object(group)
            if q_obj:
                q_objects.append(q_obj)

        if not q_objects:
            return None

        # Combine Q objects based on match type
        if match_type == 'all':
            combined = q_objects[0]
            for q_obj in q_objects[1:]:
                combined &= q_obj
            return combined
        else:  # 'any'
            combined = q_objects[0]
            for q_obj in q_objects[1:]:
                combined |= q_obj
            return combined

    def _build_rule_q_object(self, rule: Dict[str, Any]) -> Optional[Q]:
        """
        Build Q object from a single rule

        Args:
            rule: Rule dictionary with field, operator, value

        Returns:
            Q object or None
        """
        field = rule.get('field')
        operator = rule.get('operator')
        value = rule.get('value')

        if not field or not operator:
            return None

        # Handle special fields
        if field.startswith('engagement.'):
            return self._build_engagement_q_object(field, operator, value)
        elif field.startswith('deal.'):
            return self._build_deal_q_object(field, operator, value)
        elif field.startswith('custom_fields.'):
            return self._build_custom_field_q_object(field, operator, value)

        # Handle date ranges
        if operator == 'date_range' and value in self.DATE_RANGES:
            start, end = self.DATE_RANGES[value]()
            return Q(**{f'{field}__gte': start, f'{field}__lte': end})

        # Get operator function
        operator_func = self.OPERATORS.get(operator)
        if not operator_func:
            return None

        try:
            return operator_func(field, value)
        except Exception:
            return None

    def _build_engagement_q_object(self, field: str, operator: str, value: Any) -> Optional[Q]:
        """
        Build Q object for engagement-based filters

        Args:
            field: Engagement field (e.g., 'engagement.opened_last_campaign')
            operator: Filter operator
            value: Filter value

        Returns:
            Q object or None
        """
        engagement_field = field.replace('engagement.', '')

        if engagement_field == 'opened_last_campaign':
            # Contacts who opened last campaign
            return Q(
                id__in=Email.objects.filter(
                    engagement__opens_count__gt=0,
                    campaign__isnull=False
                ).values_list('recipient_contact_id', flat=True)
            )

        elif engagement_field == 'clicked_last_campaign':
            # Contacts who clicked in last campaign
            return Q(
                id__in=Email.objects.filter(
                    link_clicks__isnull=False,
                    campaign__isnull=False
                ).values_list('recipient_contact_id', flat=True)
            )

        elif engagement_field == 'not_opened_last_n_campaigns':
            # Contacts who haven't opened last N campaigns
            n = int(value) if value else 3
            return Q(
                id__in=Email.objects.filter(
                    engagement__opens_count=0,
                    campaign__isnull=False
                ).values_list('recipient_contact_id', flat=True)[:n]
            )

        elif engagement_field == 'engagement_score':
            # Filter by engagement score
            operator_func = self.OPERATORS.get(operator)
            if operator_func:
                return Q(
                    id__in=EmailEngagement.objects.filter(
                        operator_func('engagement_score', value)
                    ).values_list('email__recipient_contact_id', flat=True)
                )

        return None

    def _build_deal_q_object(self, field: str, operator: str, value: Any) -> Optional[Q]:
        """
        Build Q object for deal-based filters

        Args:
            field: Deal field (e.g., 'deal.stage')
            operator: Filter operator
            value: Filter value

        Returns:
            Q object or None
        """
        deal_field = field.replace('deal.', '')

        if deal_field == 'has_active_deal':
            return Q(deals__status='open')

        elif deal_field == 'total_deal_value':
            operator_func = self.OPERATORS.get(operator)
            if operator_func:
                return Q(
                    id__in=Contact.objects.annotate(
                        total_value=Sum('deals__value')
                    ).filter(
                        operator_func('total_value', value)
                    ).values_list('id', flat=True)
                )

        elif deal_field == 'stage':
            return Q(deals__stage__name=value)

        elif deal_field == 'won_deal_last_n_days':
            n = int(value) if value else 30
            cutoff_date = timezone.now() - timedelta(days=n)
            return Q(
                deals__status='won',
                deals__closed_date__gte=cutoff_date
            )

        return None

    def _build_custom_field_q_object(self, field: str, operator: str, value: Any) -> Optional[Q]:
        """
        Build Q object for custom field filters

        Args:
            field: Custom field (e.g., 'custom_fields.industry')
            operator: Filter operator
            value: Filter value

        Returns:
            Q object or None
        """
        custom_field_name = field.replace('custom_fields.', '')

        # Use JSONField lookups
        if operator == 'equals':
            return Q(**{f'custom_fields__{custom_field_name}': value})
        elif operator == 'contains':
            return Q(**{f'custom_fields__{custom_field_name}__icontains': value})
        elif operator == 'in':
            return Q(**{f'custom_fields__{custom_field_name}__in': value})

        return None

    def calculate_segment_size(self, filter_conditions: Dict[str, Any],
                              model_type: str = 'contact') -> int:
        """
        Calculate the size of a segment without fetching all records

        Args:
            filter_conditions: Filter conditions
            model_type: 'contact' or 'lead'

        Returns:
            Number of records matching filters
        """
        queryset = self.build_queryset(filter_conditions, model_type)
        return queryset.count()

    def preview_segment(self, filter_conditions: Dict[str, Any],
                       model_type: str = 'contact',
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get preview of segment members

        Args:
            filter_conditions: Filter conditions
            model_type: 'contact' or 'lead'
            limit: Maximum number of records to return

        Returns:
            List of record dictionaries
        """
        queryset = self.build_queryset(filter_conditions, model_type)[:limit]

        preview = []
        for record in queryset:
            preview.append({
                'id': record.id,
                'name': getattr(record, 'get_full_name', lambda: str(record))(),
                'email': record.email,
                'company': getattr(record, 'company', ''),
                'status': getattr(record, 'status', ''),
            })

        return preview

    def get_segment_recipients(self, segment) -> QuerySet:
        """
        Get all recipients for a segment

        Args:
            segment: Segment model instance

        Returns:
            QuerySet of recipients
        """
        if segment.segment_type == 'static':
            # Static segment - return pre-selected contacts
            return segment.static_contacts.all()

        elif segment.segment_type == 'dynamic':
            # Dynamic segment - build from filter conditions
            return self.build_queryset(
                segment.filter_conditions,
                model_type='contact'
            )

        elif segment.segment_type == 'behavioral':
            # Behavioral segment - based on engagement
            return self.build_queryset(
                segment.filter_conditions,
                model_type='contact'
            )

        return Contact.objects.none()

    def update_segment_size(self, segment) -> int:
        """
        Update cached segment size

        Args:
            segment: Segment model instance

        Returns:
            Updated segment size
        """
        recipients = self.get_segment_recipients(segment)
        actual_size = recipients.count()

        segment.actual_size = actual_size
        segment.last_updated_at = timezone.now()
        segment.save(update_fields=['actual_size', 'last_updated_at'])

        return actual_size

    def find_similar_contacts(self, contact, limit: int = 10) -> QuerySet:
        """
        Find contacts similar to the given contact

        Args:
            contact: Contact instance
            limit: Maximum number of similar contacts

        Returns:
            QuerySet of similar contacts
        """
        filters = Q()

        # Similar by company
        if contact.company:
            filters |= Q(company__icontains=contact.company)

        # Similar by industry (if custom field exists)
        if hasattr(contact, 'custom_fields') and contact.custom_fields.get('industry'):
            filters |= Q(custom_fields__industry=contact.custom_fields['industry'])

        # Similar by location
        if hasattr(contact, 'city') and contact.city:
            filters |= Q(city=contact.city)

        queryset = Contact.objects.filter(
            account=self.account
        ).filter(filters).exclude(id=contact.id)[:limit]

        return queryset

    def get_high_value_contacts(self, min_deal_value: float = 10000) -> QuerySet:
        """
        Get contacts with high deal values

        Args:
            min_deal_value: Minimum total deal value

        Returns:
            QuerySet of high-value contacts
        """
        return Contact.objects.filter(
            account=self.account
        ).annotate(
            total_deal_value=Sum('deals__value')
        ).filter(
            total_deal_value__gte=min_deal_value
        ).order_by('-total_deal_value')

    def get_engaged_contacts(self, min_engagement_score: int = 50) -> QuerySet:
        """
        Get highly engaged contacts

        Args:
            min_engagement_score: Minimum engagement score

        Returns:
            QuerySet of engaged contacts
        """
        engaged_contact_ids = EmailEngagement.objects.filter(
            engagement_score__gte=min_engagement_score
        ).values_list('email__recipient_contact_id', flat=True).distinct()

        return Contact.objects.filter(
            account=self.account,
            id__in=engaged_contact_ids
        )

    def get_inactive_contacts(self, days: int = 90) -> QuerySet:
        """
        Get contacts who haven't engaged in specified days

        Args:
            days: Number of days of inactivity

        Returns:
            QuerySet of inactive contacts
        """
        cutoff_date = timezone.now() - timedelta(days=days)

        # Contacts who haven't received emails or haven't engaged
        inactive_contact_ids = Contact.objects.filter(
            account=self.account
        ).exclude(
            id__in=Email.objects.filter(
                sent_at__gte=cutoff_date
            ).values_list('recipient_contact_id', flat=True)
        ).values_list('id', flat=True)

        return Contact.objects.filter(id__in=inactive_contact_ids)


def _get_last_month_range():
    """Get date range for last month"""
    today = timezone.now()
    first_of_this_month = today.replace(day=1, hour=0, minute=0, second=0)
    last_month = first_of_this_month - timedelta(days=1)
    first_of_last_month = last_month.replace(day=1)

    return (first_of_last_month, first_of_this_month)
