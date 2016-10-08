"""empty message

Revision ID: fd263851b989
Revises: bbe95d9977da
Create Date: 2016-10-08 11:32:40.999339

"""

# revision identifiers, used by Alembic.
revision = 'fd263851b989'
down_revision = 'bbe95d9977da'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(
        'targetURL',
        'value',
        existing_type=sa.String(length=2083),
        nullable=False
    )


def downgrade():
    op.alter_column(
        'targetURL',
        'value',
        existing_type=sa.String(length=2083),
        nullable=True
    )
