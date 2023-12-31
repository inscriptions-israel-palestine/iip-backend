"""Add ana to editions

Revision ID: 467e2367c2fc
Revises: a8737e1a9edd
Create Date: 2023-12-03 13:59:14.216200

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '467e2367c2fc'
down_revision = 'a8737e1a9edd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('editions', sa.Column('ana', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('editions', 'ana')
    # ### end Alembic commands ###
