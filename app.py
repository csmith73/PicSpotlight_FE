from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
import requests
import logging
import shutil
import tempfile
import weakref
import uuid
import time
from PIL import Image
import io
import numpy as np
import cv2
from numpy.lib.npyio import NpzFile
from flask_login import LoginManager, current_user, login_user, UserMixin
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash


basedir = os.path.abspath(os.path.dirname(__file__))
#basedir = basedir + '\Databases'
basedir = os.path.join(basedir, 'Databases')

class Config(object):
    DATABASE = './Databases/users.db'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'users.db')
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE
    print(SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.urandom(12)
login = LoginManager(app)
db = SQLAlchemy(app)
app.logger.debug(Config.SQLALCHEMY_DATABASE_URI)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    #username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    firstname = db.Column(db.String(64), index=True, unique=True)
    lastname = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        print(self.password_hash)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    firstname = StringField('firstname', validators=[DataRequired()])
    lastname = StringField('lastname', validators=[DataRequired()])
    #username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')



if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)



upload_file_path = './static/uploads/'
download_file_path = './static/downloads/'
download_preview_file_path = './static/downloads_preview/'
upload_preview_file_path = './static/uploads_preview/'
global_file_name = ''







@login.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, firstname=form.firstname.data, lastname=form.lastname.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    print(form.errors)
    print(form.validate_on_submit())
    print(form.username.data)
    if form.validate_on_submit():
        print('submit function called...................')
        user = User.query.filter_by(email=form.username.data).first()
        #user.set_password(form.password.data)
        if user is None or not user.check_password(form.password.data):
            print('Invalid username or password.....................')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logs')
def logs():
    #f = open('Background_Remove_Log.log')
    #f.read()
    with open('gunicorn.log', 'r') as f:
        return render_template('logs.html', text=f.read())

@app.route('/download/<img_name>')
def test_download(img_name):
    print('Test Download called.....')
    download_path = download_file_path + global_file_name
    print(download_path)
    img_name = './static/downloads/' + img_name
    print(img_name)
    resp = send_file(img_name, as_attachment=True)
    return resp




@app.route('/uploads', methods=['GET', 'POST'])
def upload():
    upload_start_time = time.time()
    if request.method == 'POST':
        img = Image.open(request.files['file'].stream)
        upload_img = img
        app.logger.debug("image.open: %s seconds ---" % (time.time() - upload_start_time))
        width, height = img.size
        img_size = (width * height)/1000000
        print(img_size)
        file_name = str(uuid.uuid4())
        upload_file_name = file_name + '.jpg'
        download_file_name = file_name + '.png'
        img.save(upload_file_path + upload_file_name)
        print('1')
        print(upload_img.size)

        newsize = (320,320)
        post_image = img.resize(newsize)
        app.logger.debug("image.save: %s seconds ---" % (time.time() - upload_start_time))
        img_io = io.BytesIO()
        post_image.save(img_io, 'JPEG', quality=100)
        app.logger.debug("bytes io image save: %s seconds ---" % (time.time() - upload_start_time))
        img_io.seek(0)
        print('2')
        print(upload_img.size)
        if img_size > .25:
            preview_img = img
            preview_img.thumbnail([600,600], Image.ANTIALIAS)
            app.logger.debug("create image preview: %s seconds ---" % (time.time() - upload_start_time))
            preview_img.save(upload_preview_file_path + upload_file_name)
            app.logger.debug("save image preview: %s seconds ---" % (time.time() - upload_start_time))

        else:
            img.save(upload_preview_file_path + upload_file_name)
            app.logger.debug("save image upload when its smallr than preview: %s seconds ---" % (time.time() - upload_start_time))

        print('3')
        print(upload_img.size)
        print('Sending image for background removal....')
        #r = requests.post('http://127.0.0.1:5001/remove_background_api', files={'file': img_io.getvalue()})
        r = requests.post('http://api.picspotlight.com/remove_background_api', files={'file': img_io.getvalue()})
        app.logger.debug("post request complete: %s seconds ---" % (time.time() - upload_start_time))
        print('Received response back from server.......')
        print(r.content)
        print(upload_img.size)
        ret_arr = io.BytesIO(r.content)
        ret_arr.seek(0)
        ret = NpzFile(ret_arr, own_fid=True, allow_pickle=True)
        print(ret.files)
        print(ret['A'].shape)


        im = Image.fromarray(ret['A'] * 255).convert('RGB')
        pil_to_cv_img = Image.open(upload_file_path + file_name + '.jpg')
        # im_np = np.array(im)
        w, h = pil_to_cv_img.size
        print(pil_to_cv_img.size)
        imo = im.resize((w, h), resample=Image.BILINEAR)
        pb_np = np.array(imo)


        opencv_image = cv2.cvtColor(np.array(pil_to_cv_img), cv2.COLOR_RGB2BGRA)
        foreground = opencv_image
        b, g, r = cv2.split(pb_np)
        foreground[:, :, 3] = b
        foreground = cv2.cvtColor(foreground, cv2.COLOR_BGRA2RGBA)
        foreground_pil = Image.fromarray(foreground)











        #returned_img = io.BytesIO(r.content)
        #app.logger.debug("bytes io convert returned image: %s seconds ---" % (time.time() - upload_start_time))
        #returned_img.seek(0)
        #returned_img = returned_img.read()
        #returned_image = Image.open(returned_img)
        #app.logger.debug("image open returned image: %s seconds ---" % (time.time() - upload_start_time))
        width, height = foreground_pil.size
        img_size_down = (width * height) / 1000000
        print(img_size_down)
        foreground_pil = foreground_pil.rotate(270)
        foreground_pil.save(download_file_path + download_file_name)
        app.logger.debug("image.save returned image: %s seconds ---" % (time.time() - upload_start_time))
        if img_size_down > .25:
            preview_img_down = foreground_pil
            preview_img_down.thumbnail([600,600], Image.ANTIALIAS)
            app.logger.debug("thumbnail create from returned image: %s seconds ---" % (time.time() - upload_start_time))

            preview_img_down.save(download_preview_file_path + download_file_name)
            app.logger.debug("image.save thumbnail of returned image: %s seconds ---" % (time.time() - upload_start_time))
            preview_img_down.close()
        else:
            foreground_pil.save(download_preview_file_path + download_file_name)

        print('Sending file to browser......')
        # if img_size_down > .25:
        #     download_html_path = '/static/downloads_preview/'+download_file_name
        # else:
        #     download_html_path = '/static/downloads/' + download_file_name
        download_html_path = '/static/downloads/' + download_file_name
        foreground_pil.close()

    return download_html_path
    #return send_file('./static/upload.png', mimetype='image/png', as_attachment='True')
    #return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')



@app.route('/process_image', methods=['POST'])
def process_image():
    if request.method == 'POST':
        print("Post received")
        img = Image.open(request.files['file'].stream)
        img.save('./static/uploads/upload.jpg')
    return "OK"

@app.route('/receive_image', methods=['POST'])
def receive_image():
    if request.method == 'POST':
        print("Post received")
        img = Image.open(request.files['file'].stream)
        img.save('./static/uploads/upload.png')
        img_io = io.BytesIO()
        img.save(img_io, 'PNG', quality=100)
        img_io.seek(0)
        print('Sending File......')
    return send_file(img_io, mimetype='image/png', as_attachment='True', attachment_filename='upload.png')

if __name__ == '__main__':
    #app.run(host='127.0.0.1', port='5000')
    app.run(host='0.0.0.0')
