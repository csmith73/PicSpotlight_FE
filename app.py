from flask import Flask, render_template, request, send_file, redirect, url_for
import os
import requests
import logging
import shutil
import tempfile
import weakref
import uuid

from PIL import Image
import io

app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)
app.logger.debug('this will show in the log')

upload_file_path = './static/uploads/'
download_file_path = './static/downloads/'
download_preview_file_path = './static/downloads_preview/'
upload_preview_file_path = './static/uploads_preview/'
global_file_name = ''

@app.route('/')
def index():
    return render_template('index.html')

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

    if request.method == 'POST':
        img = Image.open(request.files['file'].stream)
        width, height = img.size
        img_size = (width * height)/1000000
        print(img_size)
        file_name = str(uuid.uuid4())
        upload_file_name = file_name + '.jpg'
        download_file_name = file_name + '.png'
        img.save(upload_file_path + upload_file_name)
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=100)
        img_io.seek(0)
        if img_size > .25:
            preview_img = img
            preview_img.thumbnail([600,600], Image.ANTIALIAS)
            preview_img.save(upload_preview_file_path + upload_file_name)
        else:
            img.save(upload_preview_file_path + upload_file_name)


        print('Sending image for background removal....')
        r = requests.post('http://api.picspotlight.com/remove_background_api', files={'file': img_io.getvalue()})
        print('Received response back from server.......')
        #print(r.content)
        returned_img = io.BytesIO(r.content)
        returned_img.seek(0)
        #returned_img = returned_img.read()
        returned_image = Image.open(returned_img)
        width, height = returned_image.size
        img_size_down = (width * height) / 1000000
        print(img_size_down)
        returned_image.save(download_file_path + download_file_name)
        if img_size_down > .25:
            preview_img_down = returned_image
            preview_img_down.thumbnail([400,400], Image.ANTIALIAS)
            preview_img_down.save(download_preview_file_path + download_file_name)
        else:
            returned_image.save(download_preview_file_path + download_file_name)

        print('Sending file to browser......')
        # if img_size_down > .25:
        #     download_html_path = '/static/downloads_preview/'+download_file_name
        # else:
        #     download_html_path = '/static/downloads/' + download_file_name
        download_html_path = '/static/downloads/' + download_file_name
    return download_html_path
    #return send_file('./static/upload.png', mimetype='image/png', as_attachment='True')
    #return render_template('index.html')



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
    app.run(host='0.0.0.0')
