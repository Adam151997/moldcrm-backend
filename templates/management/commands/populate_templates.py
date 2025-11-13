from django.core.management.base import BaseCommand
from templates.models import BusinessTemplate


class Command(BaseCommand):
    help = 'Populate initial business templates'

    def handle(self, *args, **kwargs):
        templates_data = [
            {
                'name': 'SaaS Startup',
                'template_type': 'saas',
                'description': 'Perfect for SaaS companies tracking trials, demos, and subscriptions',
                'icon': '💻',
                'pipeline_stages': [
                    {'name': 'trial', 'display_name': 'Free Trial', 'color': '#3B82F6', 'order': 0},
                    {'name': 'demo_scheduled', 'display_name': 'Demo Scheduled', 'color': '#8B5CF6', 'order': 1},
                    {'name': 'demo_completed', 'display_name': 'Demo Completed', 'color': '#F59E0B', 'order': 2},
                    {'name': 'proposal_sent', 'display_name': 'Proposal Sent', 'color': '#F97316', 'order': 3},
                    {'name': 'negotiation', 'display_name': 'Negotiation', 'color': '#EF4444', 'order': 4},
                    {'name': 'closed_won', 'display_name': 'Subscribed', 'color': '#10B981', 'is_closed': True, 'is_won': True, 'order': 5},
                    {'name': 'closed_lost', 'display_name': 'Lost', 'color': '#6B7280', 'is_closed': True, 'is_won': False, 'order': 6},
                ],
                'custom_fields': [
                    {'name': 'mrr', 'display_name': 'Monthly Recurring Revenue', 'field_type': 'currency', 'entity_type': 'deal'},
                    {'name': 'plan_type', 'display_name': 'Plan Type', 'field_type': 'select', 'options': ['Starter', 'Professional', 'Enterprise'], 'entity_type': 'deal'},
                    {'name': 'trial_end_date', 'display_name': 'Trial End Date', 'field_type': 'date', 'entity_type': 'deal'},
                    {'name': 'team_size', 'display_name': 'Team Size', 'field_type': 'number', 'entity_type': 'contact'},
                ],
            },
            {
                'name': 'Real Estate Agency',
                'template_type': 'real_estate',
                'description': 'Manage property listings, buyers, and sales transactions',
                'icon': '🏡',
                'pipeline_stages': [
                    {'name': 'inquiry', 'display_name': 'Inquiry', 'color': '#3B82F6', 'order': 0},
                    {'name': 'property_viewing', 'display_name': 'Property Viewing', 'color': '#8B5CF6', 'order': 1},
                    {'name': 'offer_made', 'display_name': 'Offer Made', 'color': '#F59E0B', 'order': 2},
                    {'name': 'negotiation', 'display_name': 'Negotiation', 'color': '#F97316', 'order': 3},
                    {'name': 'under_contract', 'display_name': 'Under Contract', 'color': '#EF4444', 'order': 4},
                    {'name': 'closed', 'display_name': 'Sold', 'color': '#10B981', 'is_closed': True, 'is_won': True, 'order': 5},
                    {'name': 'lost', 'display_name': 'Lost', 'color': '#6B7280', 'is_closed': True, 'is_won': False, 'order': 6},
                ],
                'custom_fields': [
                    {'name': 'property_address', 'display_name': 'Property Address', 'field_type': 'text', 'entity_type': 'deal'},
                    {'name': 'property_type', 'display_name': 'Property Type', 'field_type': 'select', 'options': ['House', 'Apartment', 'Condo', 'Land', 'Commercial'], 'entity_type': 'deal'},
                    {'name': 'bedrooms', 'display_name': 'Bedrooms', 'field_type': 'number', 'entity_type': 'deal'},
                    {'name': 'bathrooms', 'display_name': 'Bathrooms', 'field_type': 'number', 'entity_type': 'deal'},
                    {'name': 'square_footage', 'display_name': 'Square Footage', 'field_type': 'number', 'entity_type': 'deal'},
                    {'name': 'financing_approved', 'display_name': 'Financing Approved', 'field_type': 'boolean', 'entity_type': 'contact'},
                ],
            },
            {
                'name': 'E-commerce Store',
                'template_type': 'ecommerce',
                'description': 'Track wholesale buyers, B2B deals, and partnerships',
                'icon': '🛒',
                'pipeline_stages': [
                    {'name': 'lead', 'display_name': 'New Lead', 'color': '#3B82F6', 'order': 0},
                    {'name': 'sample_sent', 'display_name': 'Sample Sent', 'color': '#8B5CF6', 'order': 1},
                    {'name': 'quote_requested', 'display_name': 'Quote Requested', 'color': '#F59E0B', 'order': 2},
                    {'name': 'quote_sent', 'display_name': 'Quote Sent', 'color': '#F97316', 'order': 3},
                    {'name': 'negotiation', 'display_name': 'Negotiation', 'color': '#EF4444', 'order': 4},
                    {'name': 'purchase_order', 'display_name': 'Purchase Order', 'color': '#10B981', 'is_closed': True, 'is_won': True, 'order': 5},
                    {'name': 'lost', 'display_name': 'Lost', 'color': '#6B7280', 'is_closed': True, 'is_won': False, 'order': 6},
                ],
                'custom_fields': [
                    {'name': 'order_quantity', 'display_name': 'Order Quantity', 'field_type': 'number', 'entity_type': 'deal'},
                    {'name': 'unit_price', 'display_name': 'Unit Price', 'field_type': 'currency', 'entity_type': 'deal'},
                    {'name': 'product_category', 'display_name': 'Product Category', 'field_type': 'select', 'options': ['Electronics', 'Clothing', 'Food & Beverage', 'Home & Garden', 'Other'], 'entity_type': 'deal'},
                    {'name': 'shipping_address', 'display_name': 'Shipping Address', 'field_type': 'textarea', 'entity_type': 'contact'},
                    {'name': 'preferred_payment', 'display_name': 'Preferred Payment Method', 'field_type': 'select', 'options': ['Credit Card', 'Wire Transfer', 'PayPal', 'Net 30'], 'entity_type': 'contact'},
                ],
            },
        ]

        for template_data in templates_data:
            template, created = BusinessTemplate.objects.get_or_create(
                name=template_data['name'],
                template_type=template_data['template_type'],
                defaults=template_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created template: {template.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Template already exists: {template.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully populated business templates!'))
