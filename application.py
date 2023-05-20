from flask import Flask, request, redirect, render_template, session, url_for, flash, jsonify, logging
import logging
import boto3
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook

application = Flask(__name__)
application.logger.setLevel(logging.INFO)
handler = logging.FileHandler('myapplication.log')
handler.setLevel(logging.INFO)
application.logger.addHandler(handler)
s3 = boto3.client('s3')
bucket_name = "music-bucket340822"

import utils

application.secret_key = 'your_secret_key_here'
application.config["FACEBOOK_OAUTH_CLIENT_ID"] = "148310754890459"
application.config["FACEBOOK_OAUTH_CLIENT_SECRET"] = "c319c90308ab5912c6d6afac59c6c3d7"
facebook_bp = make_facebook_blueprint()
application.register_blueprint(facebook_bp, url_prefix="/login")
@application.route('/')
def root():
    return render_template(
        'login.html')

@application.route("/login/facebook/authorized")
def facebook_authorized():
    if not facebook.authorized:
        return redirect(url_for("facebook.login"))

    # 使用 Facebook 用户信息进行业务逻辑处理，例如创建用户、登录等

    return "Successfully logged in with Facebook!"

@application.route('/login', methods=['GET', "POST"])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form['email']
    password = request.form['password']

    user = utils.validate_user(email, password)
    if user:
        session['email'] = email
        session['user_name'] = user['user_name']
        resp = redirect(url_for('forum'))
        return resp
    else:
        error_msg = 'email or password is invalid'
        return render_template('login.html', error_msg=error_msg)


@application.route('/register', methods=['GET', "POST"])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        email = request.form['email']
        user_name = request.form['user_name']
        password = request.form['password']

        if utils.is_email_exist(email):
            error_message = 'The email already exists'
            return render_template('register.html', error_msg=error_message)

        utils.insert_user(email, user_name, password)
        return redirect(url_for('login'))


@application.route('/forum', methods=['GET', "POST"])
def forum():
    user_name = session.get("user_name")
    return render_template("forum.html", user_name=user_name)
    return redirect(url_for("login"))


@application.route('/logout', methods=['GET', 'POST'])
def logout_():
    del session['email']
    del session['user_name']
    return redirect('/login')


@application.route('/perform-query', methods=['GET'])
def perform_query():
    title = request.args.get('title')
    year = request.args.get('year')
    artist = request.args.get('artist')

    if title is None:
        title = ""
    if year is None:
        year = ""
    if artist is None:
        artist = ""

    response = utils.query_music(title, year, artist)
    if response['Count'] == 0:
        return jsonify({'message': 'No result is retrieved. Please query again.'}), 200
    music_list = []
    for item in response['Items']:
        music_info = {
            'title': item['title'],
            'year': item['year'],
            'artist': item['artist']
        }
        image_url = item['img_url']
        image_name = image_url.split('/')[-1]
        image_signed_url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': image_name})
        music_info['image_url'] = image_signed_url
        music_list.applicationend(music_info)
    return jsonify( music_list)


@application.route('/subscribe', methods=['POST'])
def subscribe():
    title = request.get_json()['title']
    year = request.get_json()['year']
    artist = request.get_json()['artist']
    email = session.get('email')
    img_url = request.get_json()['img_url']
    utils.create_subscribe_table()
    utils.insert_subscribe(email,title,year,artist,img_url)
    return jsonify({'success': True})

@application.route('/remove_subscribe', methods=['POST'])
def remove_subscribe():
    title = request.get_json()['title']
    year = request.get_json()['year']
    artist = request.get_json()['artist']
    email = session.get('email')
    utils.delete_subscribe(email,title,year,artist)
    return jsonify({'success': True})


@application.route('/get_subscription', methods=['GET'])
def get_subscription():
    email = session.get('email')
    response = utils.query_subscription_by_email(email)
    music_list = []
    for item in response['Items']:

        music_info = {
            'title': item['title'],
            'year': item['year'],
            'artist': item['artist'],
            'img_url': item['img_url']
        }
        music_list.applicationend(music_info)
    return jsonify(music_list)


if __name__ == '__main__':
    application.run()
