import unittest
from app import app, db
from models import User

class TestRoutes(unittest.TestCase):

    def setUp(self):
        # Set up a test client
        app.config['TESTING'] = True
        self.client = app.test_client()

        # Create an application context
        self.app_context = app.app_context()
        self.app_context.push()

        # Create a test database (e.g., using SQLite in memory)
        db.create_all()

    def tearDown(self):
        # Clean up the test database
        db.session.remove()
        db.drop_all()

        # Pop the application context when tests are done
        self.app_context.pop()

    def login(self, username, password):
        return self.client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

    def test_route_index(self):
        # Test the index route
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Send Mass Text Messages!', response.data)

    def test_register_route(self):
        # Test the index route
        response = self.client.post('/register', data={
            'username': 'testuser',
            'password': 'testpassword',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, 200)

    def test_login_route(self):
        # Test the index route
        response = self.client.get('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
