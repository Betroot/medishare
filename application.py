from flask import Flask, request, redirect, render_template, session, url_for, flash, jsonify, logging
import boto3
import uuid
import datetime


application = Flask(__name__)

s3 = boto3.client('s3')
bucket_name = "music-bucket340822"
application.secret_key = "secret key"
import utils


@application.route('/')
def root():
    return render_template(
        'login.html')


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



# Handle the form submission and store the message data
@application.route('/post_message', methods=['POST'])
def post_message():
    content = request.form['message']
    email = session.get("email")
    user = utils.return_user_by_email(email)
    image_file = request.files['image']
    message = str(uuid.uuid4())
    latitude = request.form['latitude']
    longitude = request.form['longitude']

    phone_number = user['phone_number']
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
    if image_file:
        image_url = utils.upload_image(message + ',jpg', image_file)
    else:
        image_url = None

    utils.insert_post(message, content, image_url, latitude, longitude , user['user_name'], phone_number, timestamp)

    return redirect(url_for("forum"))

@application.route('/get_message', methods=['GET'])
def get_message():
    response = utils.query_all_post()
    result = []
    for res in response:
        message_dict = {
            'Medicine': res['content'],
            'image': res['image'],
            # 'distance': utils.compute_distance(int(res['latitude']), res['longitude'], utils.return_location()[0], utils.return_location()[1]),
            'user': res['user_name'],
            'phone_number': res['phone_number'],
            'timestamp': res['timestamp']
        }
    return jsonify(result)

@application.route('/register', methods=['GET', "POST"])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        email = request.form['email']
        user_name = request.form['user_name']
        password = request.form['password']
        phone_number = request.form['phone_number']
        if utils.return_user_by_email(email):
            error_message = 'The email already exists'
            return render_template('register.html', error_msg=error_message)

        utils.insert_user(email, user_name, password, phone_number)
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
    return jsonify(music_list)


@application.route('/remove_subscribe', methods=['POST'])
def remove_subscribe():
    title = request.get_json()['title']
    year = request.get_json()['year']
    artist = request.get_json()['artist']
    email = session.get('email')
    utils.delete_subscribe(email, title, year, artist)
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
