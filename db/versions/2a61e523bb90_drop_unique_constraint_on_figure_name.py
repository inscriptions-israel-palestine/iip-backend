"""Drop unique constraint on figure name

Revision ID: 2a61e523bb90
Revises: e6069030accb
Create Date: 2023-08-27 18:31:39.389914

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a61e523bb90'
down_revision = 'e6069030accb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("figure_name", "figures", type_="unique")


def downgrade() -> None:
    pass
