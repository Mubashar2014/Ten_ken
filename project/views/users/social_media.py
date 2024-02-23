from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, current_user

from project.extensions.extensions import db
from project.models.users import User, Post, Follow, Comment, Like

social_media_blueprint = Blueprint('social_media', __name__)


@social_media_blueprint.route('/create_post', methods=['POST'])
@jwt_required()
@swag_from('swagger/create_post.yml')  # Add this line to specify the Swagger YAML file
def create_post():
    """
    Endpoint to create a new post.

    ---
    parameters:
      - name: image
        in: formData
        type: file
        required: true
        description: The image file for the post.
      - name: description
        in: formData
        type: string
        required: true
        description: The description for the post.
    responses:
      200:
        description: Post created successfully.
    """
    image_file = request.files.get('image')
    description = request.form.get('description')

    if not image_file or not description:
        return jsonify({'error': 'Image and description are required'}), 400

    image_data = image_file.read()
    user = User.query.filter_by(id=current_user.id).first()
    new_post = Post(image=image_data, description=description, user_id=current_user.id, timestamp=datetime.now())

    db.session.add(new_post)
    db.session.commit()

    return jsonify({'message': 'Post created successfully'})

@social_media_blueprint.route('/delete_post', methods=['DELETE'])
@jwt_required()
def delete_post():
    post_id = request.form.get('post_id')
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()

    if not post:
        return jsonify({'error': 'Post not found or you do not have permission to delete it'}), 404

    db.session.delete(post)
    db.session.commit()

    return jsonify({'message': 'Post deleted successfully'})



@social_media_blueprint.route('/edit_post', methods=['PUT'])
@jwt_required()
def edit_post():
    post_id = request.form.get('post_id')
    new_description = request.form.get('description')
    new_image_file = request.files.get('image')

    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()

    if not post:
        return jsonify({'error': 'Post not found or you do not have permission to edit it'}), 404

        # Get new data from the request


    if not new_description and not new_image_file:
        return jsonify({'error': 'Description or image is required for editing'}), 400


    if new_description:
        post.description = new_description

    if new_image_file:
        new_image_data = new_image_file.read()
        post.image = new_image_data

    post.timestamp = datetime.now()
    db.session.commit()

    return jsonify({'message': 'Post edited successfully'})




@social_media_blueprint.route('/follow', methods=['POST'])
@jwt_required()
def follow_user():
    user_id = request.form.get('user_id')

    if current_user.id == user_id:
        return jsonify({'error': 'Cannot follow yourself'}), 400

    user_to_follow = User.query.get(user_id)

    if not user_to_follow:
        return jsonify({'error': 'User not found'}), 404

    if Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first():
        return jsonify({'error': 'You are already following this user'}), 400

    new_follow = Follow(follower_id=current_user.id, followed_id=user_id, timestamp=datetime.now())
    db.session.add(new_follow)
    db.session.commit()

    return jsonify({'message': f'You are now following {user_to_follow.full_name}'})


@social_media_blueprint.route('/unfollow', methods=['POST'])
@jwt_required()
def unfollow_user():

    user_id = request.args.get('user_id')

    if current_user.id == user_id:
        return jsonify({'error': 'Cannot unfollow yourself'}), 400

    user_to_unfollow = User.query.get(user_id)

    if not user_to_unfollow:
        return jsonify({'error': 'User not found'}), 404

    follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()

    if not follow:
        return jsonify({'error': 'You are not following this user'}), 400

    db.session.delete(follow)
    db.session.commit()

    return jsonify({'message': f'You have unfollowed {user_to_unfollow.full_name}'})

@social_media_blueprint.route('/followers', methods=['GET'])
@jwt_required()
def get_followers():
    user_id = request.args.get('user_id')

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    followers_query = Follow.query.filter_by(followed_id=user_id)
    followers_count = followers_query.count()

    followers = followers_query.all()
    followers_data = [{'id': follower.follower.id, 'full_name': follower.follower.full_name} for follower in followers]

    return jsonify({'followers': followers_data, 'followers_count': followers_count})

@social_media_blueprint.route('/followings', methods=['GET'])
@jwt_required()
def get_followings():
    user_id = request.args.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    followings_query = Follow.query.filter_by(follower_id=user_id)
    followings_count = followings_query.count()

    followings = followings_query.all()
    followings_data = [{'id': following.followed.id, 'full_name': following.followed.full_name} for following in
                       followings]

    return jsonify({'followings': followings_data, 'followings_count': followings_count})






@social_media_blueprint.route('/create_comment', methods=['POST'])
@jwt_required()
def create_comment():

    post_id = request.form.get('post_id')
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    text = request.form.get('text')

    if not text:
        return jsonify({'error': 'Comment text is required'}), 400

    new_comment = Comment(text=text, user_id=current_user.id, post_id=post_id, timestamp=datetime.now())
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message': 'Comment created successfully'})

@social_media_blueprint.route('/get_comments/', methods=['GET'])
def get_comments():
    post_id = request.args.get('post_id')
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    comments_query = Comment.query.filter_by(post_id=post_id)
    comments_count = comments_query.count()

    comments = comments_query.all()
    comments_data = [{'id': comment.id, 'text': comment.text, 'user_id': comment.user_id, 'timestamp': comment.timestamp} for comment in comments]

    return jsonify({'comments': comments_data, 'comments_count': comments_count})

@social_media_blueprint.route('/update_comment', methods=['PUT'])
@jwt_required()
def update_comment():

    comment_id = request.args.get('comment_id')
    comment = Comment.query.get(comment_id)

    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    if comment.user_id != current_user.id:
        return jsonify({'error': 'You do not have permission to update this comment'}), 403

    new_text = request.form.get('text')

    if not new_text:
        return jsonify({'error': 'Comment text is required'}), 400

    comment.text = new_text
    db.session.commit()

    return jsonify({'message': 'Comment updated successfully'})

@social_media_blueprint.route('/delete_comment', methods=['DELETE'])
@jwt_required()
def delete_comment():

    comment_id = request.args.get('comment_id')
    comment = Comment.query.get(comment_id)

    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    if comment.user_id != current_user.id:
        return jsonify({'error': 'You do not have permission to delete this comment'}), 403

    db.session.delete(comment)
    db.session.commit()

    return jsonify({'message': 'Comment deleted successfully'})

@social_media_blueprint.route('/like_post', methods=['POST'])
@jwt_required()
def like_post():
    post_id = request.form.get('post_id')

    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Check if the user has already liked the post
    if Like.query.filter_by(user_id=current_user.id, post_id=post_id).first():
        return jsonify({'error': 'You have already liked this post'}), 400

    new_like = Like(user_id=current_user.id, post_id=post_id, timestamp=datetime.now())
    db.session.add(new_like)
    db.session.commit()

    return jsonify({'message': 'Post liked successfully'})

@social_media_blueprint.route('/unlike_post', methods=['POST'])
@jwt_required()
def unlike_post():
    post_id = request.form.get('post_id')
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if not like:
        return jsonify({'error': 'You have not liked this post'}), 400

    db.session.delete(like)
    db.session.commit()

    return jsonify({'message': 'Post unliked successfully'})

@social_media_blueprint.route('/get_likes', methods=['GET'])
def get_likes():
    post_id = request.args.get('post_id')
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    likes_count = Like.query.filter_by(post_id=post_id).count()

    return jsonify({'likes_count': likes_count})