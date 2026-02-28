from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from ARIA.artifacts.code.models import Task
from ARIA.artifacts.code.forms import TaskForm
from ARIA.artifacts.code.app import db
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing user's tasks"""
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    
    # Build query
    query = Task.query.filter_by(user_id=current_user.id)
    
    if status_filter == 'completed':
        query = query.filter_by(completed=True)
    elif status_filter == 'pending':
        query = query.filter_by(completed=False)
    
    if priority_filter != 'all':
        query = query.filter_by(priority=priority_filter)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    # Task statistics
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    
    # Tasks by priority
    high_priority = Task.query.filter_by(user_id=current_user.id, priority='high', completed=False).count()
    medium_priority = Task.query.filter_by(user_id=current_user.id, priority='medium', completed=False).count()
    low_priority = Task.query.filter_by(user_id=current_user.id, priority='low', completed=False).count()
    
    stats = {
        'total': total_tasks,
        'completed': completed_tasks,
        'pending': pending_tasks,
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'low_priority': low_priority
    }
    
    return render_template('tasks/dashboard.html', 
                         title='Dashboard', 
                         tasks=tasks, 
                         stats=stats,
                         status_filter=status_filter,
                         priority_filter=priority_filter)

@tasks_bp.route('/task/create', methods=['GET', 'POST'])
@login_required
def create_task():
    """Create a new task"""
    form = TaskForm()
    
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash(f'Task "{task.title}" created successfully!', 'success')
        return redirect(url_for('tasks.dashboard'))
    
    return render_template('tasks/create_task.html', title='Create Task', form=form)

@tasks_bp.route('/task/<int:task_id>')
@login_required
def view_task(task_id):
    """View a specific task"""
    task = Task.query.get_or_404(task_id)
    
    # Ensure user can only view their own tasks
    if task.user_id != current_user.id:
        flash('You can only view your own tasks', 'danger')
        return redirect(url_for('tasks.dashboard'))
    
    return render_template('tasks/view_task.html', title=f'Task: {task.title}', task=task)

@tasks_bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Edit an existing task"""
    task = Task.query.get_or_404(task_id)
    
    # Ensure user can only edit their own tasks
    if task.user_id != current_user.id:
        flash('You can only edit your own tasks', 'danger')
        return redirect(url_for('tasks.dashboard'))
    
    form = TaskForm(obj=task)
    
    if form.validate_on_submit():
        form.populate_obj(task)
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Task "{task.title}" updated successfully!', 'success')
        return redirect(url_for('tasks.view_task', task_id=task.id))
    
    return render_template('tasks/edit_task.html', title='Edit Task', form=form, task=task)

@tasks_bp.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    
    # Ensure user can only delete their own tasks
    if task.user_id != current_user.id:
        flash('You can only delete your own tasks', 'danger')
        return redirect(url_for('tasks.dashboard'))
    
    title = task.title
    db.session.delete(task)
    db.session.commit()
    
    flash(f'Task "{title}" deleted successfully!', 'success')
    return redirect(url_for('tasks.dashboard'))

@tasks_bp.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    """Toggle task completion status"""
    task = Task.query.get_or_404(task_id)
    
    # Ensure user can only toggle their own tasks
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    task.completed = not task.completed
    task.updated_at = datetime.utcnow()
    db.session.commit()
    
    status = 'completed' if task.completed else 'pending'
    
    if request.is_json:
        return jsonify({
            'success': True,
            'completed': task.completed,
            'message': f'Task marked as {status}'
        })
    
    flash(f'Task marked as {status}!', 'success')
    return redirect(url_for('tasks.dashboard'))

@tasks_bp.route('/tasks/bulk-action', methods=['POST'])
@login_required
def bulk_action():
    """Perform bulk actions on tasks"""
    action = request.form.get('action')
    task_ids = request.form.getlist('task_ids')
    
    if not task_ids:
        flash('No tasks selected', 'warning')
        return redirect(url_for('tasks.dashboard'))
    
    # Convert to integers and filter user's tasks
    task_ids = [int(tid) for tid in task_ids if tid.isdigit()]
    tasks = Task.query.filter(
        Task.id.in_(task_ids),
        Task.user_id == current_user.id
    ).all()
    
    if not tasks:
        flash('No valid tasks found', 'warning')
        return redirect(url_for('tasks.dashboard'))
    
    count = len(tasks)
    
    if action == 'delete':
        for task in tasks:
            db.session.delete(task)
        flash(f'{count} task(s) deleted successfully!', 'success')
    
    elif action == 'complete':
        for task in tasks:
            task.completed = True
            task.updated_at = datetime.utcnow()
        flash(f'{count} task(s) marked as completed!', 'success')
    
    elif action == 'incomplete':
        for task in tasks:
            task.completed = False
            task.updated_at = datetime.utcnow()
        flash(f'{count} task(s) marked as pending!', 'success')
    
    else:
        flash('Invalid action', 'danger')
        return redirect(url_for('tasks.dashboard'))
    
    db.session.commit()
    return redirect(url_for('tasks.dashboard'))