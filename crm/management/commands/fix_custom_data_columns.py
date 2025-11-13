"""
Django management command to manually add missing custom_data columns
Usage: python manage.py fix_custom_data_columns
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Manually add missing custom_data columns to Lead and Contact tables'

    def handle(self, *args, **options):
        self.stdout.write('Checking and adding missing custom_data columns...\n')

        with connection.cursor() as cursor:
            # Check if columns exist first
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'crm_lead' AND column_name = 'custom_data'
            """)
            lead_custom_data_exists = cursor.fetchone() is not None

            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'crm_contact' AND column_name = 'custom_data'
            """)
            contact_custom_data_exists = cursor.fetchone() is not None

            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'crm_contact' AND column_name = 'department'
            """)
            contact_department_exists = cursor.fetchone() is not None

            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'crm_deal' AND column_name = 'custom_data'
            """)
            deal_custom_data_exists = cursor.fetchone() is not None

            # Add missing columns
            if not lead_custom_data_exists:
                self.stdout.write('Adding custom_data to crm_lead...')
                cursor.execute("""
                    ALTER TABLE crm_lead
                    ADD COLUMN custom_data JSONB DEFAULT '{}' NOT NULL
                """)
                self.stdout.write(self.style.SUCCESS('✓ Added custom_data to crm_lead'))
            else:
                self.stdout.write(self.style.WARNING('⚠ crm_lead.custom_data already exists'))

            if not contact_custom_data_exists:
                self.stdout.write('Adding custom_data to crm_contact...')
                cursor.execute("""
                    ALTER TABLE crm_contact
                    ADD COLUMN custom_data JSONB DEFAULT '{}' NOT NULL
                """)
                self.stdout.write(self.style.SUCCESS('✓ Added custom_data to crm_contact'))
            else:
                self.stdout.write(self.style.WARNING('⚠ crm_contact.custom_data already exists'))

            if not contact_department_exists:
                self.stdout.write('Adding department to crm_contact...')
                cursor.execute("""
                    ALTER TABLE crm_contact
                    ADD COLUMN department VARCHAR(100) DEFAULT '' NOT NULL
                """)
                self.stdout.write(self.style.SUCCESS('✓ Added department to crm_contact'))
            else:
                self.stdout.write(self.style.WARNING('⚠ crm_contact.department already exists'))

            if not deal_custom_data_exists:
                self.stdout.write('Adding custom_data to crm_deal...')
                cursor.execute("""
                    ALTER TABLE crm_deal
                    ADD COLUMN custom_data JSONB DEFAULT '{}' NOT NULL
                """)
                self.stdout.write(self.style.SUCCESS('✓ Added custom_data to crm_deal'))
            else:
                self.stdout.write(self.style.WARNING('⚠ crm_deal.custom_data already exists'))

        self.stdout.write(self.style.SUCCESS('\n✓ Database schema update complete!'))
        self.stdout.write('You can now restart your application.')
