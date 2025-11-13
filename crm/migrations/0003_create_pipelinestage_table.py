# Generated manually to fix missing PipelineStage table on Railway

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_table_if_not_exists(apps, schema_editor):
    """Create PipelineStage table if it doesn't exist"""
    from django.db import connection

    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'crm_pipelinestage'
            );
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            # Create the table
            cursor.execute("""
                CREATE TABLE "crm_pipelinestage" (
                    "id" bigserial NOT NULL PRIMARY KEY,
                    "name" varchar(100) NOT NULL,
                    "display_name" varchar(100) NOT NULL,
                    "color" varchar(20) NOT NULL DEFAULT 'blue',
                    "is_closed" boolean NOT NULL DEFAULT false,
                    "is_won" boolean NOT NULL DEFAULT false,
                    "order" integer NOT NULL DEFAULT 0,
                    "created_at" timestamp with time zone NOT NULL,
                    "updated_at" timestamp with time zone NOT NULL,
                    "account_id" bigint NOT NULL
                );
            """)

            # Add foreign key constraint
            cursor.execute("""
                ALTER TABLE "crm_pipelinestage"
                ADD CONSTRAINT "crm_pipelinestage_account_id_fkey"
                FOREIGN KEY ("account_id")
                REFERENCES "accounts_account"("id")
                DEFERRABLE INITIALLY DEFERRED;
            """)

            # Create unique constraint
            cursor.execute("""
                ALTER TABLE "crm_pipelinestage"
                ADD CONSTRAINT "crm_pipelinestage_account_id_name_uniq"
                UNIQUE ("account_id", "name");
            """)

            # Create index on account_id
            cursor.execute("""
                CREATE INDEX "crm_pipelinestage_account_id_idx"
                ON "crm_pipelinestage" ("account_id");
            """)

            # Create index for ordering
            cursor.execute("""
                CREATE INDEX "crm_pipelinestage_order_idx"
                ON "crm_pipelinestage" ("order");
            """)


def reverse_func(apps, schema_editor):
    """No need to reverse - if table exists, keep it"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_add_custom_data_to_models'),
    ]

    operations = [
        migrations.RunPython(create_table_if_not_exists, reverse_func),
    ]
