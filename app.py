from flask import Flask, render_template, request, send_file
import os
import requests
import logging

from PIL import Image
import io

app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)
app.logger.debug('this will show in the log')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads', methods=['GET', 'POST'])
def upload():

    if request.method == 'POST':
        img = Image.open(request.files['file'].stream)
        #img.save('./static/uploads/upload.jpg')
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=100)
        img_io.seek(0)
        print('Sending image for background removal....')
        r = requests.post('http://127.0.0.1:5001/remove_background_api', files={'file': img_io.getvalue()})
        print('Received response back from server.......')
        print(r.content)
        returned_img = io.BytesIO(r.content)
        returned_img.seek(0)
        #returned_img = returned_img.read()
        returned_image = Image.open(returned_img)
        returned_image.save('./static/uploads/upload.png')
        print('Sending file to browser......')
    return send_file('./static/uploads/upload.png', mimetype='image/png', as_attachment='True')



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
    app.run(host='127.0.0.1',port='5000')
