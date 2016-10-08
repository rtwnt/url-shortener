"""empty message

Revision ID: a92d9d023624
Revises: f819f3f77f30
Create Date: 2016-10-08 01:17:30.083109

"""

# revision identifiers, used by Alembic.
revision = 'a92d9d023624'
down_revision = 'f819f3f77f30'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.rename_table('shortenedURL', 'targetURL')

def downgrade():
    op.rename_table('targetURL', 'shortenedURL')
