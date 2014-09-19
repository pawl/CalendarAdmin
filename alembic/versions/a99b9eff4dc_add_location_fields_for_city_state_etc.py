"""add location fields for city, state, etc

Revision ID: a99b9eff4dc
Revises: 31d1635c3462
Create Date: 2014-09-19 00:55:07.638543

"""

# revision identifiers, used by Alembic.
revision = 'a99b9eff4dc'
down_revision = '31d1635c3462'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('location', sa.Column('address', sa.String(length=255)))
    op.add_column('location', sa.Column('city', sa.String(length=255)))
    op.add_column('location', sa.Column('country', sa.String(length=2)))
    op.add_column('location', sa.Column('state', sa.String(length=2)))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('location', 'state')
    op.drop_column('location', 'country')
    op.drop_column('location', 'city')
    op.drop_column('location', 'address')
    ### end Alembic commands ###
