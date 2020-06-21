from flask import Flask, render_template, request, send_file
import os
import requests

from PIL import Image
import io

app = Flask(__name__)

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
        r = requests.post('http://127.0.0.1:5000/process_image', files={'file': img_io.getvalue()})
        print(r.text)

        return "OK"



@app.route('/process_image', methods=['POST'])
def process_image():
    if request.method == 'POST':
        print("Post received")
        img = Image.open(request.files['file'].stream)
        img.save('./static/uploads/upload.jpg')
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0')
