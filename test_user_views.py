"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest -q test_user_views.py


import os
from unittest import TestCase
from sqlalchemy.orm.exc import NoResultFound
from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
ctx = app.app_context()
ctx.push()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        
        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
    
    def test_list_users(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/users')

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertIn('@testuser', html)
    
    def test_show_user(self):
         """Test the user profile page"""
         with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            #test logged in users page
            resp = c.get(f'/users/{sess[CURR_USER_KEY]}')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('testuser', html)
            self.assertIn('Edit Profile', html)
            self.assertIn('Delete Profile', html)

            #test not logged in users page

            u = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser3",
                                    image_url=None)
            db.session.commit()
            resp2 = c.get(f'/users/{u.id}')
            html = resp2.get_data(as_text=True)
            self.assertEqual(resp2.status_code, 200)
            self.assertIn('testuser2', html)
            self.assertNotIn('Edit Profile', html)
            self.assertNotIn('Delete Profile', html)
        
    def test_show_following(self):
        """Test the following page"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            u = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser3",
                                    image_url=None)
            
            db.session.commit()

            self.testuser.following.append(u)

            db.session.commit()

            resp = c.get(f'/users/{sess[CURR_USER_KEY]}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser2', html)

            #test when not logged in
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]

            resp = c.get(f'/users/{u.id}/following')
            self.assertEqual(resp.status_code, 302)

    def test_show_followers(self):
        """Test the followers page"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            u = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser3",
                                    image_url=None)
            
            db.session.commit()

            self.testuser.followers.append(u)

            db.session.commit()

            resp = c.get(f'/users/{sess[CURR_USER_KEY]}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser2', html)

            #test when not logged in
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]

            resp = c.get(f'/users/{u.id}/followers')
            self.assertEqual(resp.status_code, 302)

    def test_follow_user(self):
         """Test the follow post route"""
         with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            u = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser3",
                                    image_url=None)
            
            db.session.commit()

            resp = c.post(f'/users/follow/{u.id}')

            self.assertEqual(resp.status_code, 302)

            self.assertIn(u, self.testuser.following)

            #test when not logged in
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]
            resp = c.post(f'/users/follow/{u.id}')
            self.assertEqual(resp.status_code, 302)

    def test_stop_following(self):
        """Test the stop following post route"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            u = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser3",
                                    image_url=None)
            
            db.session.commit()

            self.testuser.following.append(u)
            db.session.commit()

            resp = c.post(f'/users/stop-following/{u.id}')
            self.assertEqual(resp.status_code, 302)

            self.assertNotIn(u, self.testuser.following)

            #test not signed in
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]
            resp = c.post(f'/users/stop-following/{u.id}')
            self.assertEqual(resp.status_code, 302)

    def test_show_edit_user(self):
        """test showing the edit form for a user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
        resp = c.get('/users/profile')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('testuser', html)
        self.assertIn('test@test.com', html)
        self.assertIn('username', html)
        self.assertIn('email', html)
        self.assertIn('To confirm changes, enter your password:', html)

        #test not signed in
        with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]
        resp = c.get('/users/profile')
        self.assertEqual(resp.status_code, 302)

    def test_post_edit_user(self):
        """test the post route of editing a user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
        resp = c.post('/users/profile', data={"username": "JOSEPH",
                                              "email": "super@gmail.com",
                                              "bio": "SUPER DUPER AWESOME",
                                              "image_url": None,
                                              "header_image_url": None,
                                              "password": "testuser"})
        
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(self.testuser.username, "JOSEPH")
        self.assertEqual(self.testuser.email, "super@gmail.com")
        self.assertEqual(self.testuser.bio, "SUPER DUPER AWESOME")

        #test not signed in
        with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]
        resp = c.post('/users/profile', data={"username": "JOSEPH1",
                                              "email": "super1@gmail.com",
                                              "bio": "SUPER DUPER AWESOME",
                                              "image_url": None,
                                              "header_image_url": None,
                                              "password": "testuser"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.testuser.username, "JOSEPH")
        self.assertEqual(self.testuser.email, "super@gmail.com")

    def test_delete_user(self):
         """test deleting the current user"""
         with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            id = self.testuser.id
            resp = c.post('/users/delete')
            self.assertEqual(resp.status_code, 302)
            users = User.query.all()
            users_ids = [user.id for user in users]
            
            self.assertNotIn(id, users_ids)

            
            
        
            

        
            





            

        


    

    
            




    




            









            