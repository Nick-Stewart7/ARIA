import unittest
import json
from datetime import datetime, timedelta
from ARIA.artifacts.code.app import create_app, db
from ARIA.artifacts.code.models import User, Role, Task

class TaskManagerTestCase(unittest.TestCase):
    """Base test case for Task Manager application"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        db.create_all()
        
        # Create test roles
        self.admin_role = Role(name='admin', description='Administrator')
        self.user_role = Role(name='user', description='Regular User')
        db.session.add(self.admin_role)
        db.session.add(self.user_role)
        db.session.commit()
        
        # Create test users
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            role_id=self.user_role.id
        )
        self.test_user.set_password('testpass123')
        
        self.test_admin = User(
            username='testadmin',
            email='admin@example.com',
            role_id=self.admin_role.id
        )
        self.test_admin.set_password('adminpass123')
        
        db.session.add(self.test_user)
        db.session.add(self.test_admin)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after each test method"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, username, password):
        """Helper method to log in a user"""
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    def logout(self):
        """Helper method to log out a user"""
        return self.client.get('/logout', follow_redirects=True)

class AuthTestCase(TaskManagerTestCase):
    """Test cases for authentication functionality"""
    
    def test_user_registration(self):
        """Test user registration"""
        response = self.client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        
        # Check if user was created
        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('newpass123'))
    
    def test_duplicate_user_registration(self):
        """Test registration with duplicate username"""
        response = self.client.post('/register', data={
            'username': 'testuser',  # Already exists
            'email': 'different@example.com',
            'password': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertEqual(response.status_code, 200)  # Should stay on registration page
        self.assertIn(b'Username already taken', response.data)
    
    def test_user_login_logout(self):
        """Test user login and logout"""
        # Test login
        response = self.login('testuser', 'testpass123')
        self.assertEqual(response.status_code, 200)
        
        # Test logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = self.login('testuser', 'wrongpassword')
        self.assertIn(b'Invalid username or password', response.data)
    
    def test_password_change(self):
        """Test password change functionality"""
        self.login('testuser', 'testpass123')
        
        response = self.client.post('/change-password', data={
            'current_password': 'testpass123',
            'new_password': 'newpass456',
            'new_password2': 'newpass456'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Test login with new password
        self.logout()
        response = self.login('testuser', 'newpass456')
        self.assertEqual(response.status_code, 200)

class TaskTestCase(TaskManagerTestCase):
    """Test cases for task functionality"""
    
    def setUp(self):
        """Set up test fixtures with sample tasks"""
        super().setUp()
        
        # Create sample tasks
        self.task1 = Task(
            title='Test Task 1',
            description='First test task',
            priority='high',
            user_id=self.test_user.id
        )
        self.task2 = Task(
            title='Test Task 2',
            description='Second test task',
            priority='medium',
            completed=True,
            user_id=self.test_user.id
        )
        self.task3 = Task(
            title='Admin Task',
            description='Admin only task',
            priority='low',
            user_id=self.test_admin.id
        )
        
        db.session.add(self.task1)
        db.session.add(self.task2)
        db.session.add(self.task3)
        db.session.commit()
    
    def test_task_creation(self):
        """Test task creation through web interface"""
        self.login('testuser', 'testpass123')
        
        response = self.client.post('/task/create', data={
            'title': 'New Task',
            'description': 'New task description',
            'priority': 'high',
            'completed': False
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        
        # Check if task was created
        task = Task.query.filter_by(title='New Task').first()
        self.assertIsNotNone(task)
        self.assertEqual(task.user_id, self.test_user.id)
        self.assertEqual(task.priority, 'high')
        self.assertFalse(task.completed)
    
    def test_task_editing(self):
        """Test task editing functionality"""
        self.login('testuser', 'testpass123')
        
        response = self.client.post(f'/task/{self.task1.id}/edit', data={
            'title': 'Updated Task Title',
            'description': 'Updated description',
            'priority': 'low',
            'completed': True
        })
        self.assertEqual(response.status_code, 302)  # Redirect after update
        
        # Check if task was updated
        updated_task = Task.query.get(self.task1.id)
        self.assertEqual(updated_task.title, 'Updated Task Title')
        self.assertEqual(updated_task.priority, 'low')
        self.assertTrue(updated_task.completed)
    
    def test_task_deletion(self):
        """Test task deletion"""
        self.login('testuser', 'testpass123')
        
        response = self.client.post(f'/task/{self.task1.id}/delete')
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        
        # Check if task was deleted
        deleted_task = Task.query.get(self.task1.id)
        self.assertIsNone(deleted_task)
    
    def test_task_toggle(self):
        """Test task completion toggle"""
        self.login('testuser', 'testpass123')
        
        original_status = self.task1.completed
        response = self.client.post(f'/task/{self.task1.id}/toggle')
        self.assertEqual(response.status_code, 302)  # Redirect after toggle
        
        # Check if task status was toggled
        updated_task = Task.query.get(self.task1.id)
        self.assertEqual(updated_task.completed, not original_status)
    
    def test_task_access_control(self):
        """Test that users can only access their own tasks"""
        self.login('testuser', 'testpass123')
        
        # Try to access admin's task
        response = self.client.get(f'/task/{self.task3.id}')
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Try to edit admin's task
        response = self.client.post(f'/task/{self.task3.id}/edit', data={
            'title': 'Hacked Task'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect

class APITestCase(TaskManagerTestCase):
    """Test cases for REST API functionality"""
    
    def setUp(self):
        """Set up test fixtures for API testing"""
        super().setUp()
        
        # Create sample task
        self.task = Task(
            title='API Test Task',
            description='Task for API testing',
            priority='medium',
            user_id=self.test_user.id
        )
        db.session.add(self.task)
        db.session.commit()
    
    def test_api_get_tasks(self):
        """Test GET /api/tasks"""
        self.login('testuser', 'testpass123')
        
        response = self.client.get('/api/tasks')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('tasks', data)
        self.assertGreater(len(data['tasks']), 0)
    
    def test_api_create_task(self):
        """Test POST /api/tasks"""
        self.login('testuser', 'testpass123')
        
        task_data = {
            'title': 'API Created Task',
            'description': 'Created via API',
            'priority': 'high'
        }
        
        response = self.client.post('/api/tasks',
                                  data=json.dumps(task_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['task']['title'], 'API Created Task')
    
    def test_api_update_task(self):
        """Test PUT /api/tasks/<id>"""
        self.login('testuser', 'testpass123')
        
        update_data = {
            'title': 'Updated via API',
            'completed': True
        }
        
        response = self.client.put(f'/api/tasks/{self.task.id}',
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['task']['title'], 'Updated via API')
        self.assertTrue(data['task']['completed'])
    
    def test_api_delete_task(self):
        """Test DELETE /api/tasks/<id>"""
        self.login('testuser', 'testpass123')
        
        response = self.client.delete(f'/api/tasks/{self.task.id}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify task was deleted
        deleted_task = Task.query.get(self.task.id)
        self.assertIsNone(deleted_task)
    
    def test_api_validation(self):
        """Test API input validation"""
        self.login('testuser', 'testpass123')
        
        # Test creating task without title
        invalid_data = {
            'description': 'No title provided'
        }
        
        response = self.client.post('/api/tasks',
                                  data=json.dumps(invalid_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_api_unauthorized_access(self):
        """Test API access without authentication"""
        # Don't log in
        response = self.client.get('/api/tasks')
        self.assertEqual(response.status_code, 401)

class SecurityTestCase(TaskManagerTestCase):
    """Test cases for security features"""
    
    def test_csrf_protection(self):
        """Test CSRF token protection"""
        self.login('testuser', 'testpass123')
        
        # Try to create task without CSRF token
        response = self.client.post('/task/create', data={
            'title': 'CSRF Test Task',
            'description': 'Should fail without CSRF token'
        }, environ_base={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        
        # Should be rejected due to missing CSRF token
        self.assertIn(response.status_code, [400, 403])
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        user = User.query.filter_by(username='testuser').first()
        
        # Password should not be stored in plain text
        self.assertNotEqual(user.password_hash, 'testpass123')
        
        # Should be able to verify password
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.check_password('wrongpassword'))
    
    def test_session_management(self):
        """Test session management"""
        # Login should create a session
        response = self.login('testuser', 'testpass123')
        self.assertEqual(response.status_code, 200)
        
        # Should be able to access protected pages
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Logout should clear session
        self.logout()
        
        # Should not be able to access protected pages
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)  # Redirect to login

class ValidationTestCase(TaskManagerTestCase):
    """Test cases for input validation"""
    
    def test_form_validation(self):
        """Test form field validation"""
        self.login('testuser', 'testpass123')
        
        # Test empty title
        response = self.client.post('/task/create', data={
            'title': '',
            'description': 'Valid description'
        })
        self.assertEqual(response.status_code, 200)  # Should stay on form
        
        # Test title too long
        response = self.client.post('/task/create', data={
            'title': 'x' * 201,  # Over 200 character limit
            'description': 'Valid description'
        })
        self.assertEqual(response.status_code, 200)  # Should stay on form
        
        # Test invalid priority
        response = self.client.post('/task/create', data={
            'title': 'Valid title',
            'priority': 'invalid'
        })
        self.assertEqual(response.status_code, 200)  # Should stay on form
    
    def test_email_validation(self):
        """Test email format validation"""
        response = self.client.post('/register', data={
            'username': 'newuser2',
            'email': 'invalid-email',  # Invalid email format
            'password': 'validpass123',
            'password2': 'validpass123'
        })
        self.assertEqual(response.status_code, 200)  # Should stay on form
        self.assertIn(b'Invalid email address', response.data)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(AuthTestCase))
    test_suite.addTest(unittest.makeSuite(TaskTestCase))
    test_suite.addTest(unittest.makeSuite(APITestCase))
    test_suite.addTest(unittest.makeSuite(SecurityTestCase))
    test_suite.addTest(unittest.makeSuite(ValidationTestCase))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with error code if tests failed
    exit(0 if result.wasSuccessful() else 1)