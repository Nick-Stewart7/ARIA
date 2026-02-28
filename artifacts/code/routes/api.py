from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from ARIA.artifacts.code.models import Task, User
from ARIA.artifacts.code.app import db
from datetime import datetime
import logging

api_bp = Blueprint('api', __name__)

# Error handlers
@api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401

@api_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden'}), 403

@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

def validate_task_data(data, required_fields=['title']):
    """Validate task data"""
    errors = []
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f'{field} is required')
    
    # Validate field types and constraints
    if 'title' in data and len(data['title'].strip()) == 0:
        errors.append('Title cannot be empty')
    elif 'title' in data and len(data['title']) > 200:
        errors.append('Title must be less than 200 characters')
    
    if 'description' in data and data['description'] and len(data['description']) > 1000:
        errors.append('Description must be less than 1000 characters')
    
    if 'priority' in data and data['priority'] not in ['low', 'medium', 'high']:
        errors.append('Priority must be one of: low, medium, high')
    
    if 'completed' in data and not isinstance(data['completed'], bool):
        errors.append('Completed must be a boolean value')
    
    return errors

# Tasks API endpoints
@api_bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Get all tasks for the current user"""
    try:
        # Get query parameters
        completed = request.args.get('completed')
        priority = request.args.get('priority')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        
        # Build query
        query = Task.query.filter_by(user_id=current_user.id)
        
        if completed is not None:
            completed_bool = completed.lower() in ['true', '1', 'yes']
            query = query.filter_by(completed=completed_bool)
        
        if priority and priority in ['low', 'medium', 'high']:
            query = query.filter_by(priority=priority)
        
        # Apply pagination
        paginated_tasks = query.order_by(Task.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        tasks = [task.to_dict() for task in paginated_tasks.items]
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'pagination': {
                'page': page,
                'pages': paginated_tasks.pages,
                'per_page': per_page,
                'total': paginated_tasks.total,
                'has_next': paginated_tasks.has_next,
                'has_prev': paginated_tasks.has_prev
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting tasks: {str(e)}')
        return jsonify({'error': 'Failed to retrieve tasks'}), 500

@api_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate data
        errors = validate_task_data(data)
        if errors:
            return jsonify({'error': 'Validation failed', 'messages': errors}), 400
        
        # Create task
        task = Task(
            title=data['title'].strip(),
            description=data.get('description', '').strip() or None,
            priority=data.get('priority', 'medium'),
            completed=data.get('completed', False),
            user_id=current_user.id
        )
        
        # Handle due_date if provided
        if 'due_date' in data and data['due_date']:
            try:
                task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid due_date format. Use ISO format.'}), 400
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating task: {str(e)}')
        return jsonify({'error': 'Failed to create task'}), 500

@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """Get a specific task"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # Ensure user can only access their own tasks
        if task.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting task {task_id}: {str(e)}')
        return jsonify({'error': 'Failed to retrieve task'}), 500

@api_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Update a specific task"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # Ensure user can only update their own tasks
        if task.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate data (title not required for updates)
        errors = validate_task_data(data, required_fields=[])
        if errors:
            return jsonify({'error': 'Validation failed', 'messages': errors}), 400
        
        # Update task fields
        task.update_from_dict(data)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task updated successfully',
            'task': task.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating task {task_id}: {str(e)}')
        return jsonify({'error': 'Failed to update task'}), 500

@api_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Delete a specific task"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # Ensure user can only delete their own tasks
        if task.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        task_title = task.title
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Task "{task_title}" deleted successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting task {task_id}: {str(e)}')
        return jsonify({'error': 'Failed to delete task'}), 500

@api_bp.route('/tasks/<int:task_id>/toggle', methods=['PATCH'])
@login_required
def toggle_task_completion(task_id):
    """Toggle task completion status"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # Ensure user can only toggle their own tasks
        if task.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        task.completed = not task.completed
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = 'completed' if task.completed else 'pending'
        
        return jsonify({
            'success': True,
            'message': f'Task marked as {status}',
            'task': task.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling task {task_id}: {str(e)}')
        return jsonify({'error': 'Failed to toggle task'}), 500

# User API endpoints
@api_bp.route('/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    """Get current user's profile"""
    try:
        return jsonify({
            'success': True,
            'user': current_user.to_dict()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting user profile: {str(e)}')
        return jsonify({'error': 'Failed to retrieve profile'}), 500

@api_bp.route('/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get user's task statistics"""
    try:
        total_tasks = Task.query.filter_by(user_id=current_user.id).count()
        completed_tasks = Task.query.filter_by(user_id=current_user.id, completed=True).count()
        pending_tasks = total_tasks - completed_tasks
        
        # Tasks by priority
        high_priority = Task.query.filter_by(user_id=current_user.id, priority='high', completed=False).count()
        medium_priority = Task.query.filter_by(user_id=current_user.id, priority='medium', completed=False).count()
        low_priority = Task.query.filter_by(user_id=current_user.id, priority='low', completed=False).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'high_priority_tasks': high_priority,
                'medium_priority_tasks': medium_priority,
                'low_priority_tasks': low_priority
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f'Error getting user stats: {str(e)}')
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

# Health check endpoint
@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200