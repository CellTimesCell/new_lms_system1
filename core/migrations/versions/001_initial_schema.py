"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-04-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('preferred_language', sa.String(), nullable=False, default='en'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )

    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.String(), nullable=True),
        sa.Column('profile_picture', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=False, default='UTC'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create role_permissions table
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create courses table
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, default=False),
        sa.Column('instructor_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['instructor_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    # Create modules table
    op.create_table(
        'modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create course_modules association table
    op.create_table(
        'course_modules',
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('course_id', 'module_id')
    )

    # Create content_items table
    op.create_table(
        'content_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create enrollments table
    op.create_table(
        'enrollments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('enrollment_date', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('completion_status', sa.String(), nullable=False, default='not_started'),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'course_id')
    )

    # Create rubrics table
    op.create_table(
        'rubrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create assignments table
    op.create_table(
        'assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('available_from', sa.DateTime(), nullable=True),
        sa.Column('available_until', sa.DateTime(), nullable=True),
        sa.Column('points_possible', sa.Float(), nullable=False, default=100.0),
        sa.Column('submission_type', sa.String(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, default=False),
        sa.Column('allow_late_submissions', sa.Boolean(), nullable=False, default=True),
        sa.Column('late_submission_penalty', sa.Float(), nullable=False, default=0.0),
        sa.Column('rubric_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rubric_id'], ['rubrics.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create rubric_criteria table
    op.create_table(
        'rubric_criteria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rubric_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('points_possible', sa.Float(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['rubric_id'], ['rubrics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create rating_levels table
    op.create_table(
        'rating_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('criterion_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('points', sa.Float(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['criterion_id'], ['rubric_criteria.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create submissions table
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('submission_text', sa.Text(), nullable=True),
        sa.Column('submission_files', sa.JSON(), nullable=True),
        sa.Column('is_late', sa.Boolean(), nullable=False, default=False),
        sa.Column('status', sa.String(), nullable=False, default='submitted'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create grades table
    op.create_table(
        'grades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('grader_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('rubric_scores', sa.JSON(), nullable=True),
        sa.Column('graded_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['grader_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indices
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_courses_title'), 'courses', ['title'], unique=False)
    op.create_index(op.f('ix_modules_title'), 'modules', ['title'], unique=False)
    op.create_index(op.f('ix_content_items_title'), 'content_items', ['title'], unique=False)
    op.create_index(op.f('ix_assignments_title'), 'assignments', ['title'], unique=False)
    op.create_index(op.f('ix_rubrics_title'), 'rubrics', ['title'], unique=False)
    op.create_index(op.f('ix_role_permissions_permission'), 'role_permissions', ['permission'], unique=False)

    # Insert default roles
    op.execute(
        """
        INSERT INTO roles (name, description) VALUES
        ('admin', 'Administrator with full system access'),
        ('instructor', 'Teacher role with course management permissions'),
        ('student', 'Student role with learning permissions')
        """
    )

    # Insert default permissions
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission) VALUES
        (1, 'users:create'), (1, 'users:read'), (1, 'users:update'), (1, 'users:delete'),
        (1, 'courses:create'), (1, 'courses:read'), (1, 'courses:update'), (1, 'courses:delete'),
        (1, 'assignments:create'), (1, 'assignments:read'), (1, 'assignments:update'), (1, 'assignments:delete'),
        (1, 'grades:create'), (1, 'grades:read'), (1, 'grades:update'), (1, 'grades:delete'),
        (1, 'analytics:read'),
        (2, 'courses:create'), (2, 'courses:read'), (2, 'courses:update'),
        (2, 'assignments:create'), (2, 'assignments:read'), (2, 'assignments:update'),
        (2, 'grades:create'), (2, 'grades:read'), (2, 'grades:update'),
        (2, 'analytics:read'),
        (3, 'courses:read'),
        (3, 'assignments:read'),
        (3, 'assignments:submit'),
        (3, 'grades:read')
        """
    )


def downgrade():
    # Drop all tables in reverse order
    op.drop_table('grades')
    op.drop_table('submissions')
    op.drop_table('rating_levels')
    op.drop_table('rubric_criteria')
    op.drop_table('assignments')
    op.drop_table('rubrics')
    op.drop_table('enrollments')
    op.drop_table('content_items')
    op.drop_table('course_modules')
    op.drop_table('modules')
    op.drop_table('courses')
    op.drop_table('role_permissions')
    op.drop_table('user_profiles')
    op.drop_table('user_roles')
    op.drop_table('roles')
    op.drop_table('users')