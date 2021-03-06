"""mm

Revision ID: d609054a879a
Revises: 
Create Date: 2020-11-23 09:32:09.231203

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd609054a879a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bike',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('plate_number', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('branch', sa.Integer(), nullable=False),
    sa.Column('serial_number', sa.String(length=100), nullable=False),
    sa.Column('date_added', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('plate_number'),
    sa.UniqueConstraint('serial_number')
    )
    op.create_table('branch',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reminder',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user', sa.String(length=255), nullable=False),
    sa.Column('notified', sa.Boolean(), nullable=True),
    sa.Column('date_added', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('severity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('weight', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('branch_reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('branch', sa.Integer(), nullable=False),
    sa.Column('severity', sa.Integer(), nullable=True),
    sa.Column('category', sa.Integer(), nullable=True),
    sa.Column('comments', sa.Text(), nullable=True),
    sa.Column('date_added', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['branch'], ['branch.id'], ),
    sa.ForeignKeyConstraint(['category'], ['category.id'], ),
    sa.ForeignKeyConstraint(['severity'], ['severity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('branch', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['branch'], ['branch.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    op.drop_table('branch_reports')
    op.drop_table('severity')
    op.drop_table('reminder')
    op.drop_table('category')
    op.drop_table('branch')
    op.drop_table('bike')
    # ### end Alembic commands ###
