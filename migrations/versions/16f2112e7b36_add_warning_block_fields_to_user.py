"""Add warning/block fields to User

Revision ID: 16f2112e7b36
Revises: 66dbbfa6bad5
Create Date: 2025-05-23 14:50:13.628982

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16f2112e7b36'
down_revision = '66dbbfa6bad5'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite batch mode
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column(
            'toxic_warning_count',
            sa.Integer(),
            nullable=False,
            server_default='0'    # <<— here
        ))
        batch_op.add_column(sa.Column(
            'last_warning_time',
            sa.DateTime(),
            nullable=True
        ))
        batch_op.add_column(sa.Column(
            'login_block_until',
            sa.DateTime(),
            nullable=True
        ))

def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('login_block_until')
        batch_op.drop_column('last_warning_time')
        batch_op.drop_column('toxic_warning_count')

    # ### end Alembic commands ###
