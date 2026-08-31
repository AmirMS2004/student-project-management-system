"""add admin role

Revision ID: cc0c09881608
Revises: 5fde7409659f
Create Date: 2026-08-23 04:25:53.012531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc0c09881608'
down_revision: Union[str, None] = '5fde7409659f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Alembic's autogenerate does not detect changes to the allowed values of an
# Enum column, so this migration (adding "ADMIN" to the user role enum) is
# written by hand. SQLite can't ALTER a CHECK constraint in place, so we use
# batch mode, which recreates the table under the hood.


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column(
            'role',
            existing_type=sa.Enum('PROFESSOR', 'STUDENT', name='userrole'),
            type_=sa.Enum('PROFESSOR', 'STUDENT', 'ADMIN', name='userrole'),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column(
            'role',
            existing_type=sa.Enum('PROFESSOR', 'STUDENT', 'ADMIN', name='userrole'),
            type_=sa.Enum('PROFESSOR', 'STUDENT', name='userrole'),
            existing_nullable=False,
        )
