# Generated manually to fix missing Activity and Note tables on Railway

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_tables_if_not_exist(apps, schema_editor):
    """Create Activity and Note tables if they don't exist"""
    from django.db import connection

    with connection.cursor() as cursor:
        # Check if Activity table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'crm_activity'
            );
        """)
        activity_exists = cursor.fetchone()[0]

        if not activity_exists:
            # Create the Activity table
            cursor.execute("""
                CREATE TABLE "crm_activity" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "activity_type" varchar(20) NOT NULL,
                    "title" varchar(200) NOT NULL,
                    "description" text NOT NULL,
                    "due_date" timestamp with time zone NULL,
                    "completed" boolean NOT NULL DEFAULT false,
                    "completed_at" timestamp with time zone NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "account_id" bigint NOT NULL,
                    "contact_id" bigint NULL,
                    "created_by_id" bigint NOT NULL,
                    "deal_id" bigint NULL,
                    "lead_id" bigint NULL
                );
            """)

            # Add foreign key constraints for Activity
            cursor.execute("""
                ALTER TABLE "crm_activity"
                ADD CONSTRAINT "crm_activity_account_id_fkey"
                FOREIGN KEY ("account_id")
                REFERENCES "accounts_account"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            cursor.execute("""
                ALTER TABLE "crm_activity"
                ADD CONSTRAINT "crm_activity_contact_id_fkey"
                FOREIGN KEY ("contact_id")
                REFERENCES "crm_contact"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            cursor.execute("""
                ALTER TABLE "crm_activity"
                ADD CONSTRAINT "crm_activity_created_by_id_fkey"
                FOREIGN KEY ("created_by_id")
                REFERENCES "users_user"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            cursor.execute("""
                ALTER TABLE "crm_activity"
                ADD CONSTRAINT "crm_activity_deal_id_fkey"
                FOREIGN KEY ("deal_id")
                REFERENCES "crm_deal"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            cursor.execute("""
                ALTER TABLE "crm_activity"
                ADD CONSTRAINT "crm_activity_lead_id_fkey"
                FOREIGN KEY ("lead_id")
                REFERENCES "crm_lead"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            # Create indexes for Activity
            cursor.execute("""
                CREATE INDEX "crm_activity_account_id_idx" ON "crm_activity" ("account_id");
            """)
            cursor.execute("""
                CREATE INDEX "crm_activity_contact_id_idx" ON "crm_activity" ("contact_id");
            """)
            cursor.execute("""
                CREATE INDEX "crm_activity_created_by_id_idx" ON "crm_activity" ("created_by_id");
            """)
            cursor.execute("""
                CREATE INDEX "crm_activity_deal_id_idx" ON "crm_activity" ("deal_id");
            """)
            cursor.execute("""
                CREATE INDEX "crm_activity_lead_id_idx" ON "crm_activity" ("lead_id");
            """)

        # Check if Note table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'crm_note'
            );
        """)
        note_exists = cursor.fetchone()[0]

        if not note_exists:
            # Create the Note table
            cursor.execute("""
                CREATE TABLE "crm_note" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "content" text NOT NULL,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "account_id" bigint NOT NULL,
                    "contact_id" bigint NULL,
                    "created_by_id" bigint NOT NULL,
                    "deal_id" bigint NULL,
                    "lead_id" bigint NULL
                );
            """)

            # Add foreign key constraints for Note
            cursor.execute("""
                ALTER TABLE "crm_note"
                ADD CONSTRAINT "crm_note_account_id_fkey"
                FOREIGN KEY ("account_id")
                REFERENCES "accounts_account"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            cursor.execute("""
                ALTER TABLE "crm_note"
                ADD CONSTRAINT "crm_note_contact_id_fkey"
                FOREIGN KEY ("contact_id")
                REFERENCES "crm_contact"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            cursor.execute("""
                ALTER TABLE "crm_note"
                ADD CONSTRAINT "crm_note_created_by_id_fkey"
                FOREIGN KEY ("created_by_id")
                REFERENCES "users_user"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            cursor.execute("""
                ALTER TABLE "crm_note"
                ADD CONSTRAINT "crm_note_deal_id_fkey"
                FOREIGN KEY ("deal_id")
                REFERENCES "crm_deal"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            cursor.execute("""
                ALTER TABLE "crm_note"
                ADD CONSTRAINT "crm_note_lead_id_fkey"
                FOREIGN KEY ("lead_id")
                REFERENCES "crm_lead"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            # Create indexes for Note
            cursor.execute("""
                CREATE INDEX "crm_note_account_id_idx" ON "crm_note" ("account_id");
            """)
            cursor.execute("""
                CREATE INDEX "crm_note_contact_id_idx" ON "crm_note" ("contact_id");
            """)
            cursor.execute("""
                CREATE INDEX "crm_note_created_by_id_idx" ON "crm_note" ("created_by_id");
            """)
            cursor.execute("""
                CREATE INDEX "crm_note_deal_id_idx" ON "crm_note" ("deal_id");
            """)
            cursor.execute("""
                CREATE INDEX "crm_note_lead_id_idx" ON "crm_note" ("lead_id");
            """)


def reverse_func(apps, schema_editor):
    """No need to reverse - if tables exist, keep them"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0004_deal_pipeline_stage'),
    ]

    operations = [
        migrations.RunPython(create_tables_if_not_exist, reverse_func),
    ]
