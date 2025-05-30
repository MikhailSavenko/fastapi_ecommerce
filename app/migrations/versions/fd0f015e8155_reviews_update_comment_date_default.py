"""Reviews update comment_date default

Revision ID: fd0f015e8155
Revises: 6dd647041f62
Create Date: 2025-03-24 15:24:04.694775

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fd0f015e8155'
down_revision: Union[str, None] = '6dd647041f62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('reviews', 'comment_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('reviews', 'comment_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    # ### end Alembic commands ###
