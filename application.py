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
    message = request.form['message']
    email = session.get("email")
    user = utils.return_user_by_email(email)
    image_file = request.files['image']
    message_id = str(uuid.uuid4())
    address = request.form['address']
    phone_number = user['phone_number']
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
    if image_file:
        image_url = utils.upload_image(message_id + '.jpg', image_file)
    else:
        image_url = None

    utils.insert_post(message_id, message, image_url, address, user['user_name'], phone_number, timestamp)

    return redirect(url_for("forum"))


@application.route('/get_message', methods=['GET'])
def get_message():
    response = utils.query_all_post()
    result = []
    for res in response:
        message_dict = {
            'medicine': res['message'],
            'image': res['image'],
            'address': res['address'],
            'user': res['user_name'],
            'phone_number': res['phone_number'],
            'timestamp': res['timestamp']
        }
        result.append(message_dict)
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

@application.route('/remove_message', methods=['POST'])
def remove_message():
    medicine = request.get_json()['medicine']
    timestamp = request.get_json()['timestamp']
    user_name = request.get_json()['user_name']
    print("medicine: ")
    print(medicine)
    if(user_name == session.get('user_name')):
        utils.delete_post(medicine, timestamp)
    return jsonify({'success': True})


if __name__ == '__main__':
    application.run()
