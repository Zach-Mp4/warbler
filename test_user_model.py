"""User model tests."""

# run these tests like:
#
#    python -m unittest -q test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from psycopg2.errors import UniqueViolation
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# python -m unittest test_user_model

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    
    def test_repr(self):
        """Test the representation method of the user model"""

        #<User #{self.id}: {self.username}, {self.email}>

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        m = u.__repr__()

        self.assertEqual(m, f'<User #{u.id}: testuser, test@test.com>')

    def test_is_following(self):
        """test if is_following successfully detect when user1 is following user2"""
        
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test@test2.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)

        db.session.commit()

        u1.following.append(u2)

        check = u1.is_following(u2)

        self.assertEqual(check, 1)

    def test_is_not_following(self):
        """test if is_following successfully detect when user1 is NOT following user2"""
        
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test@test2.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)

        db.session.commit()


        check = u1.is_following(u2)

        self.assertNotEqual(check, 1)

    def test_is_followed_by(self):
        """test if is_followed_by successfully detect when user2 is following user1"""
        
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test@test2.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)

        u2.followers.append(u1)

        db.session.commit()
        
        check = u1.is_followed_by(u2)

        self.assertEqual(check, 1)

    def test_is_followed_by(self):
        """test if is_followed_by successfully detect when user2 is not following user1"""
        
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test@test2.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)

        db.session.commit()
        
        check = u1.is_followed_by(u2)

        self.assertNotEqual(check, 1)

    def test_signup(self):
        """test if signup creates user if given proper credentials"""

        u1 = User.signup(email="test@test1.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url= None)
        db.session.commit()

        self.assertIsInstance(u1, User)
    
    def test_authenticate(self):
        """test the authenticate method"""

        u = u1 = User.signup(email="test@test1.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url= None)
        db.session.commit()

        u_login = User.authenticate(username = 'testuser', password = "HASHED_PASSWORD")

        self.assertIsInstance(u_login, User)

        u_fail_username = User.authenticate(username = 'testuser1', password = 'HASHED_PASSWORD')

        self.assertFalse(u_fail_username)

        u_fail_password = User.authenticate(username = 'testuser', password = 'HASHED_PASSWORD11')

        self.assertFalse(u_fail_username)