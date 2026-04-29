"""Convert identifier columns to UUID

Revision ID: 0003_convert_ids_to_uuid
Revises: 0002_case_insensitive_list_names
Create Date: 2026-04-29
"""

from alembic import op

revision = "0003_convert_ids_to_uuid"
down_revision = "0002_case_insensitive_list_names"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'users'
                  AND column_name = 'id'
                  AND data_type <> 'uuid'
            ) THEN
                ALTER TABLE oauth_identities DROP CONSTRAINT IF EXISTS
                    oauth_identities_user_id_fkey;
                ALTER TABLE project_lists DROP CONSTRAINT IF EXISTS
                    project_lists_user_id_fkey;
                ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_user_id_fkey;
                ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_list_id_fkey;
                ALTER TABLE notification_acks DROP CONSTRAINT IF EXISTS
                    notification_acks_user_id_fkey;
                ALTER TABLE notification_acks DROP CONSTRAINT IF EXISTS
                    notification_acks_task_id_fkey;

                DROP INDEX IF EXISTS ix_project_lists_user_lower_name;

                ALTER TABLE users ALTER COLUMN id TYPE uuid USING id::uuid;
                ALTER TABLE oauth_identities ALTER COLUMN id TYPE uuid USING id::uuid;
                ALTER TABLE oauth_identities ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
                ALTER TABLE project_lists ALTER COLUMN id TYPE uuid USING id::uuid;
                ALTER TABLE project_lists ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
                ALTER TABLE tasks ALTER COLUMN id TYPE uuid USING id::uuid;
                ALTER TABLE tasks ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
                ALTER TABLE tasks ALTER COLUMN list_id TYPE uuid USING list_id::uuid;
                ALTER TABLE notification_acks ALTER COLUMN id TYPE uuid USING id::uuid;
                ALTER TABLE notification_acks ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
                ALTER TABLE notification_acks ALTER COLUMN task_id TYPE uuid USING task_id::uuid;

                ALTER TABLE oauth_identities ADD CONSTRAINT oauth_identities_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                ALTER TABLE project_lists ADD CONSTRAINT project_lists_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                ALTER TABLE tasks ADD CONSTRAINT tasks_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                ALTER TABLE tasks ADD CONSTRAINT tasks_list_id_fkey
                    FOREIGN KEY (list_id) REFERENCES project_lists(id) ON DELETE CASCADE;
                ALTER TABLE notification_acks ADD CONSTRAINT notification_acks_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                ALTER TABLE notification_acks ADD CONSTRAINT notification_acks_task_id_fkey
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE;

                CREATE UNIQUE INDEX ix_project_lists_user_lower_name
                    ON project_lists (user_id, lower(name));
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'users'
                  AND column_name = 'id'
                  AND data_type = 'uuid'
            ) THEN
                ALTER TABLE oauth_identities DROP CONSTRAINT IF EXISTS
                    oauth_identities_user_id_fkey;
                ALTER TABLE project_lists DROP CONSTRAINT IF EXISTS
                    project_lists_user_id_fkey;
                ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_user_id_fkey;
                ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_list_id_fkey;
                ALTER TABLE notification_acks DROP CONSTRAINT IF EXISTS
                    notification_acks_user_id_fkey;
                ALTER TABLE notification_acks DROP CONSTRAINT IF EXISTS
                    notification_acks_task_id_fkey;

                DROP INDEX IF EXISTS ix_project_lists_user_lower_name;

                ALTER TABLE users ALTER COLUMN id TYPE varchar(36) USING id::text;
                ALTER TABLE oauth_identities ALTER COLUMN id TYPE varchar(36) USING id::text;
                ALTER TABLE oauth_identities ALTER COLUMN user_id TYPE varchar(36)
                    USING user_id::text;
                ALTER TABLE project_lists ALTER COLUMN id TYPE varchar(36) USING id::text;
                ALTER TABLE project_lists ALTER COLUMN user_id TYPE varchar(36)
                    USING user_id::text;
                ALTER TABLE tasks ALTER COLUMN id TYPE varchar(36) USING id::text;
                ALTER TABLE tasks ALTER COLUMN user_id TYPE varchar(36) USING user_id::text;
                ALTER TABLE tasks ALTER COLUMN list_id TYPE varchar(36) USING list_id::text;
                ALTER TABLE notification_acks ALTER COLUMN id TYPE varchar(36) USING id::text;
                ALTER TABLE notification_acks ALTER COLUMN user_id TYPE varchar(36)
                    USING user_id::text;
                ALTER TABLE notification_acks ALTER COLUMN task_id TYPE varchar(36)
                    USING task_id::text;

                ALTER TABLE oauth_identities ADD CONSTRAINT oauth_identities_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                ALTER TABLE project_lists ADD CONSTRAINT project_lists_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                ALTER TABLE tasks ADD CONSTRAINT tasks_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                ALTER TABLE tasks ADD CONSTRAINT tasks_list_id_fkey
                    FOREIGN KEY (list_id) REFERENCES project_lists(id) ON DELETE CASCADE;
                ALTER TABLE notification_acks ADD CONSTRAINT notification_acks_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                ALTER TABLE notification_acks ADD CONSTRAINT notification_acks_task_id_fkey
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE;

                CREATE UNIQUE INDEX ix_project_lists_user_lower_name
                    ON project_lists (user_id, lower(name));
            END IF;
        END $$;
        """
    )
