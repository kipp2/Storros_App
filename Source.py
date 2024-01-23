from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storroz.db'
db = SQLAlchemy(app)

# Define database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255))  # Assuming URLs for simplicity
    bio = db.Column(db.Text)
    private_status = db.Column(db.Boolean, default=False)
    verified_status = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='user', lazy=True)
    followers = db.relationship('Follower', backref='user', lazy=True, foreign_keys='Follower.following_id')
    following = db.relationship('Follower', backref='follower', lazy=True, foreign_keys='Follower.follower_id')
    likes = db.relationship('Like', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='post', lazy=True, foreign_keys=['Notification.user_id', 'Notification.another_foreign_key'])

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_type = db.Column(db.String(10), nullable=False)  # 'Storroz, a pic or a video 
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    location = db.Column(db.String(50), nullable=True)
    hashtags = db.relationship('Hashtag', secondary='post_hashtag', backref='posts', lazy='dynamic')


class Follower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Hashtag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

post_hashtag_association = db.Table('post_hashtag',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('hashtag_id', db.Integer, db.ForeignKey('hashtag.id'))
)        

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PostHashtag(db.Model):
    __tablename__ = 'post_hashtag'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    hashtag_id = db.Column(db.Integer, db.ForeignKey('hashtag.id'), nullable=False)
    __table_args__ = {'extend_existing': True}

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    another_foreign_key = db.Column(db.Integer, db.ForeignKey('another_model.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    # Explicit Foreign keys
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_notifications')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_notifications')
    post = db.relationship('Post')
    another_model = db.relationship('AnotherModel', foreign_keys=[another_foreign_key], backref='notifications')

# Create tables
with app.app_context():
    db.create_all()

# API Endpoints

# User Endpoints
# 1. register_User 
@app.route('/api/users/register', methods=['POST'])
def register_user():
    data = request.json

    # Extract user information from the request
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Check if username or email already exists in the database
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'message': 'Username or email already exists'}), 400

    # Create a new user
    new_user = User(username=username, email=email)
    new_user.set_password(password)

    # Add the user to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# . Login_user 
@app.route('/api/users/login', methods=['POST'])
def login_user():
    data = request.json
    # Validate login data, check credentials, generate token, etc.
    # For simplicity, you may want to use a token-based authentication system
    # (e.g., JWT) for handling user authentication and authorization
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        # Return token or user information based on your authentication mechanism
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

# 3. User Profile
# GET user profile
@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if user:
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'profile_picture': user.profile_picture,
            'bio': user.bio,
            'private_status': user.private_status,
            'verified_status': user.verified_status
        }
        return jsonify({'user': user_info})
    else:
        return jsonify({'message': 'User not found'}), 404
    
    # PUT update user profile
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user_profile(user_id):
    user = User.query.get(user_id)
    if user:
        data = request.json
        # Update user profile information
        user.bio = data.get('bio', user.bio)
        user.profile_picture = data.get('profile_picture', user.profile_picture)
        user.private_status = data.get('private_status', user.private_status)
        # Commit changes to the database
        db.session.commit()
        return jsonify({'message': 'User profile updated successfully'})
    else:
        return jsonify({'message': 'User not found'}), 404
    
# 4. User Follow
@app.route('/api/users/<int:user_id>/follow', methods=['POST'])
def follow_user(user_id):
    data = request.json
    follower_id = data.get('follower_id')
    if follower_id:
        new_follower = Follower(
            follower_id=follower_id,
            following_id=user_id
        )
        db.session.add(new_follower)
        db.session.commit()
        return jsonify({'message': 'User followed successfully'}), 201
    else:
        return jsonify({'message': 'Follower ID not provided'}), 400
    
# 5. User Unfollow
@app.route('/api/users/<int:user_id>/unfollow', methods=['POST'])
def unfollow_user(user_id):
    data = request.json
    follower_id = data.get('follower_id')
    if follower_id:
        follower = Follower.query.filter_by(follower_id=follower_id, following_id=user_id).first()
        if follower:
            db.session.delete(follower)
            db.session.commit()
            return jsonify({'message': 'User unfollowed successfully'})
        else:
            return jsonify({'message': 'User is not being followed by the specified follower'}), 400
    else:
        return jsonify({'message': 'Follower ID not provided'}), 400
    
# 6. User Followers
@app.route('/api/users/<int:user_id>/followers', methods=['GET'])
def get_user_followers(user_id):
    user = User.query.get(user_id)
    if user:
        followers_list = [{'follower_id': follower.follower_id, 'timestamp': follower.timestamp.isoformat()}
                          for follower in user.followers]
        return jsonify({'followers': followers_list})
    else:
        return jsonify({'message': 'User not found'}), 404
    
# 7. User Following
@app.route('/api/users/<int:user_id>/following', methods=['GET'])
def get_user_following(user_id):
    user = User.query.get(user_id)
    if user:
        following_list = [{'following_id': following.following_id, 'timestamp': following.timestamp.isoformat()}
                           for following in user.following]
        return jsonify({'following': following_list})
    else:
        return jsonify({'message': 'User not found'}), 404
    
@app.route('/signin', methods=['GET'])
def render_signin_form():
    return render_template('signin.html')
    
# API Endpoints for Posts

# 1. Create a Post
@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.json
    new_post = Post(
        user_id=data['user_id'],
        post_type=data['post_type'],
        content=data['content'],
        location=data.get('location')
    )
    db.session.add(new_post)
    db.session.commit()
    return jsonify({'message': 'Post created successfully'}), 201

# 2. Get Post Details
@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post_details(post_id):
    post = Post.query.get(post_id)
    if post:
        post_info = {
            'id': post.id,
            'user_id': post.user_id,
            'post_type': post.post_type,
            'content': post.content,
            'timestamp': post.timestamp.isoformat(),
            'location': post.location
        }
        return jsonify({'post': post_info})
    else:
        return jsonify({'message': 'Post not found'}), 404

# 3. Like a Post
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    data = request.json
    post = Post.query.get(post_id)
    if post:
        new_like = Like(
            user_id=data['user_id'],
            post_id=post_id
        )
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'message': 'Post liked successfully'}), 201
    else:
        return jsonify({'message': 'Post not found'}), 404

# 4. Unlike a Post
@app.route('/api/posts/<int:post_id>/like', methods=['DELETE'])
def unlike_post(post_id):
    data = request.json
    post = Post.query.get(post_id)
    if post:
        like = Like.query.filter_by(user_id=data['user_id'], post_id=post_id).first()
        if like:
            db.session.delete(like)
            db.session.commit()
            return jsonify({'message': 'Post unliked successfully'})
        else:
            return jsonify({'message': 'User did not like this post'}), 400
    else:
        return jsonify({'message': 'Post not found'}), 404

# 5. Comment on a Post
@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def comment_on_post(post_id):
    data = request.json
    post = Post.query.get(post_id)
    if post:
        new_comment = Comment(
            user_id=data['user_id'],
            post_id=post_id,
            content=data['content']
        )
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({'message': 'Comment added successfully'}), 201
    else:
        return jsonify({'message': 'Post not found'}), 404

# 6. Get Post Comments
@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    post = Post.query.get(post_id)
    if post:
        comments_list = [
            {'user_id': comment.user_id, 'content': comment.content, 'timestamp': comment.timestamp.isoformat()}
            for comment in post.comments
        ]
        return jsonify({'comments': comments_list})
    else:
        return jsonify({'message': 'Post not found'}), 404
    
# API Endpoints for Hashtags

# 1. Get Trending Hashtags
@app.route('/api/hashtags/trending', methods=['GET'])
def get_trending_hashtags():
    # Fetch trending hashtags based on your criteria (e.g., most used in recent posts)
    # For simplicity, let's assume you have a function get_trending_hashtags() that returns a list of trending hashtags
    trending_hashtags = get_trending_hashtags()
    return jsonify({'trending_hashtags': trending_hashtags})

# 2. Search Hashtags
@app.route('/api/hashtags/search', methods=['GET'])
def search_hashtags():
    query = request.args.get('q')
    if query:
        # Perform a search for hashtags containing the query
        # For simplicity, let's assume you have a function search_hashtags(query) that returns a list of matching hashtags
        matching_hashtags = search_hashtags(query)
        return jsonify({'matching_hashtags': matching_hashtags})
    else:
        return jsonify({'message': 'Query parameter "q" is required for hashtag search'}), 400

# API Endpoints for Notifications

# 1. Get Notifications
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    # Assuming you want notifications for the currently authenticated user
    # Modify this based on your authentication mechanism
    user_id = get_user_profile()
    if user_id:
        user = User.query.get(user_id)
        if user:
            notifications_list = [
                {
                    'id': notification.id,
                    'sender_id': notification.sender_id,
                    'receiver_id': notification.receiver_id,
                    'post_id': notification.post_id,
                    'content': notification.content,
                    'timestamp': notification.timestamp.isoformat(),
                    'is_read': notification.is_read
                } for notification in user.notifications_received
            ]
            return jsonify({'notifications': notifications_list})
        else:
            return jsonify({'message': 'User not found'}), 404
    else:
        return jsonify({'message': 'Authentication required'}), 401

# 2. Mark Notification as Read
@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_as_read(notification_id):
    # Assuming you want to mark a notification as read for the currently authenticated user
    # Modify this based on your authentication mechanism
    user_id = get_user_profile()
    if user_id:
        notification = Notification.query.get(notification_id)
        if notification and notification.receiver_id == user_id:
            notification.is_read = True
            db.session.commit()
            return jsonify({'message': 'Notification marked as read successfully'})
        else:
            return jsonify({'message': 'Notification not found or does not belong to the user'}), 404
    else:
        return jsonify({'message': 'Authentication required'}), 401


# Explore page Endponts 
@app.route('/api/explore', methods=['GET'])
def explore_content():
    # Fetch and return content for the explore page based on your criteria
    # For simplicity, let's assume you have a function get_explore_content() that returns a list of content
    explore_content = get_explore_content()
    return jsonify({'explore_content': explore_content})

# API Endpoints for Search

# 1. Search Users
@app.route('/api/search/users', methods=['GET'])
def search_users():
    query = request.args.get('q')
    if query:
        # Perform a search for users based on the query
        # For simplicity, let's assume you have a function search_users(query) that returns a list of matching users
        matching_users = search_users(query)
        return jsonify({'matching_users': matching_users})
    else:
        return jsonify({'message': 'Query parameter "q" is required for user search'}), 400

# 2. Search Posts
@app.route('/api/search/posts', methods=['GET'])
def search_posts():
    query = request.args.get('q')
    if query:
        # Perform a search for posts based on the query
        # For simplicity, let's assume you have a function search_posts(query) that returns a list of matching posts
        matching_posts = search_posts(query)
        return jsonify({'matching_posts': matching_posts})
    else:
        return jsonify({'message': 'Query parameter "q" is required for post search'}), 400

# 3. Search Hashtags
@app.route('/api/search/hashtags', methods=['GET'])
def search_hash():
    query = request.args.get('q')
    if query:
        # Perform a search for hashtags based on the query
        # For simplicity, let's assume you have a function search_hashtags(query) that returns a list of matching hashtags
        matching_hashtags = search_hashtags(query)
        return jsonify({'matching_hashtags': matching_hashtags})
    else:
        return jsonify({'message': 'Query parameter "q" is required for hashtag search'}), 400
    
# API Endpoints for Live Stream

# 1. Start Live Stream
@app.route('/api/live/stream/start', methods=['POST'])
def start_live_stream():
    data = request.json
    user_id = data.get('user_id')
    if user_id:
        # Check if the user exists
        user = User.query.get(user_id)
        if user:
            # You can implement your live stream start logic here
            # For simplicity, let's assume you have a function start_live_stream(user_id) that returns a stream key or URL
            stream_key = start_live_stream(user_id)
            return jsonify({'stream_key': stream_key, 'message': 'Live stream started successfully'}), 200
        else:
            return jsonify({'message': 'User not found'}), 404
    else:
        return jsonify({'message': 'User ID is required for starting a live stream'}), 400

# 2. End Live Stream
@app.route('/api/live/stream/end', methods=['POST'])
def end_live_stream():
    data = request.json
    user_id = data.get('user_id')
    if user_id:
        # Check if the user exists
        user = User.query.get(user_id)
        if user:
            # You can implement your live stream end logic here
            # For simplicity, let's assume you have a function end_live_stream(user_id) that stops the live stream
            end_live_stream(user_id)
            return jsonify({'message': 'Live stream ended successfully'}), 200
        else:
            return jsonify({'message': 'User not found'}), 404
    else:
        return jsonify({'message': 'User ID is required for ending a live stream'}), 400
    
# API Endpoint for Editing Post Media

# Edit Post Media
@app.route('/api/posts/<int:post_id>/edit-media', methods=['PUT'])
def edit_post_media(post_id):
    data = request.json
    post = Post.query.get(post_id)
    if post:
        # Update post media information
        post.content = data.get('content', post.content)
        post.location = data.get('location', post.location)

        # Commit changes to the database
        db.session.commit()
        return jsonify({'message': 'Post media edited successfully'})
    else:
        return jsonify({'message': 'Post not found'}), 404
    
# API Endpoint for Cross-Platform Sharing

# Share Post to Other Platforms
@app.route('/api/posts/<int:post_id>/share', methods=['POST'])
def share_post_to_other_platforms(post_id):
    data = request.json
    post = Post.query.get(post_id)
    
    if post:
        # Assuming you have a function to handle cross-platform sharing logic
        success = share_post_to_other_platforms_logic(post, data)
        
        if success:
            return jsonify({'message': 'Post shared to other platforms successfully'})
        else:
            return jsonify({'message': 'Failed to share post to other platforms'}), 500
    else:
        return jsonify({'message': 'Post not found'}), 404
    
# API Endpoints for Analytics and Insight

# 1. Get Post Analytics
@app.route('/api/posts/<int:post_id>/analytics', methods=['GET'])
def get_post_analytics(post_id):
    post = Post.query.get(post_id)
    if post:
        # Assuming you have a function to retrieve post analytics
        post_analytics = get_post_analytics_data(post)
        return jsonify({'post_analytics': post_analytics})
    else:
        return jsonify({'message': 'Post not found'}), 404

# 2. Get User Insights
@app.route('/api/users/<int:user_id>/insights', methods=['GET'])
def get_user_insights(user_id):
    user = User.query.get(user_id)
    if user:
        # Assuming you have a function to retrieve user insights
        user_insights = get_user_insights_data(user)
        return jsonify({'user_insights': user_insights})
    else:
        return jsonify({'message': 'User not found'}), 404


# API Endpoint for Privacy Setting

# Update Privacy Setting
@app.route('/api/users/<int:user_id>/privacy', methods=['PUT'])
def update_privacy_setting(user_id):
    data = request.json
    user = User.query.get(user_id)
    if user:
        # Update user privacy setting
        user.private_status = data.get('private_status', user.private_status)
        # Commit changes to the database
        db.session.commit()
        return jsonify({'message': 'User privacy setting updated successfully'})
    else:
        return jsonify({'message': 'User not found'}), 404
    


if __name__ == '__main__':
    app.run(debug=True)


