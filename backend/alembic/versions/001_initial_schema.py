"""initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('role', sa.Enum('designer', 'admin', name='userrole'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    op.create_table('designs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('original_filename', sa.String(), nullable=False),
    sa.Column('original_dpi', sa.Float(), nullable=True),
    sa.Column('width_px', sa.Integer(), nullable=True),
    sa.Column('height_px', sa.Integer(), nullable=True),
    sa.Column('upload_storage_path', sa.String(), nullable=False),
    sa.Column('upscaled_storage_path', sa.String(), nullable=True),
    sa.Column('status', sa.Enum('uploaded', 'processing', 'review', 'approved', 'exported', name='designstatus'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_designs_id'), 'designs', ['id'], unique=False)
    op.create_index(op.f('ix_designs_status'), 'designs', ['status'], unique=False)
    op.create_index(op.f('ix_designs_user_id'), 'designs', ['user_id'], unique=False)
    
    op.create_table('jobs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('design_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('status', sa.Enum('queued', 'upscaling', 'segmenting', 'clustering', 'building', 'generating', 'done', 'failed', name='jobstatus'), nullable=False),
    sa.Column('current_step', sa.Integer(), nullable=False),
    sa.Column('total_steps', sa.Integer(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['design_id'], ['designs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_design_id'), 'jobs', ['design_id'], unique=False)
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    
    op.create_table('layers',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('design_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('layer_index', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('role', sa.Enum('background', 'motif', name='layerrole'), nullable=False),
    sa.Column('hex_color', sa.String(length=7), nullable=False),
    sa.Column('lab_l', sa.Float(), nullable=False),
    sa.Column('lab_a', sa.Float(), nullable=False),
    sa.Column('lab_b', sa.Float(), nullable=False),
    sa.Column('pixel_count', sa.Integer(), nullable=False),
    sa.Column('coverage_percent', sa.Float(), nullable=False),
    sa.Column('mask_storage_path', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['design_id'], ['designs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_layers_design_id'), 'layers', ['design_id'], unique=False)
    op.create_index(op.f('ix_layers_id'), 'layers', ['id'], unique=False)
    
    op.create_table('colorways',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('design_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('variant_index', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('variant_type', sa.Enum('motif_only', 'bg_only', 'full', 'manual', name='colorwaytype'), nullable=False),
    sa.Column('color_map', sa.JSON(), nullable=False),
    sa.Column('tif_storage_path', sa.String(), nullable=False),
    sa.Column('preview_storage_path', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['design_id'], ['designs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_colorways_design_id'), 'colorways', ['design_id'], unique=False)
    op.create_index(op.f('ix_colorways_id'), 'colorways', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_colorways_id'), table_name='colorways')
    op.drop_index(op.f('ix_colorways_design_id'), table_name='colorways')
    op.drop_table('colorways')
    
    op.drop_index(op.f('ix_layers_id'), table_name='layers')
    op.drop_index(op.f('ix_layers_design_id'), table_name='layers')
    op.drop_table('layers')
    
    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_design_id'), table_name='jobs')
    op.drop_table('jobs')
    
    op.drop_index(op.f('ix_designs_user_id'), table_name='designs')
    op.drop_index(op.f('ix_designs_status'), table_name='designs')
    op.drop_index(op.f('ix_designs_id'), table_name='designs')
    op.drop_table('designs')
    
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    sa.Enum(name='colorwaytype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='layerrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='jobstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='designstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
