"""empty message

Revision ID: bbe95d9977da
Revises: a92d9d023624
Create Date: 2016-10-08 11:01:04.912494

"""

# revision identifiers, used by Alembic.
revision = 'bbe95d9977da'
down_revision = 'a92d9d023624'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(
        'targetURL',
        'target',
        new_column_name='value',
        existing_type=sa.String(length=2083),
        existing_nullable=True
    )


def downgrade():
    op.alter_column(
        'targetURL',
        'value',
        new_column_name='target',
        existing_type=sa.String(length=2083),
        existing_nullable=True
    )
