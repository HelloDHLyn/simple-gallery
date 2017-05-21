import atexit
import os
import uuid

import psycopg2
import requests
from flask import Flask, redirect, render_template, session, url_for, request, json

from config.db import *

app = Flask(__name__)
conn = psycopg2.connect(host=DB_HOST, dbname=DB_DATABASE, user=DB_USERNAME, password=DB_PASSWORD)
cursor = conn.cursor()


@app.route('/')
def welcome():
    if 'session_id' not in session:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('main'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    로그인 화면.
    :return: 
    """
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        password = request.form['password']

        r = requests.post('https://api.lynlab.co.kr/v1/auth', json={"name": "lynlab_gallery", "passcode": password})
        response = json.loads(r.text)

        if response['result']:
            session['session_id'] = uuid.uuid4()
            return redirect(url_for('main'))
        else:
            return redirect(url_for('login'))


@app.route('/main')
def main():
    """
    메인 화면.
    :return:
    """
    if 'session_id' not in session:
        return redirect(url_for('login'))

    # 사진 그룹을 불러온다.
    cursor.execute('SELECT * FROM gallery_photo_group ORDER BY \"order\"')

    import boto3

    groups = []
    for name, bucket, prefix, order in cursor.fetchall():
        client = boto3.client("s3")
        response = client.list_objects(Bucket=bucket, Prefix=f"{prefix}/thumbnails")

        photos = []
        for photo in filter(lambda p: p.get('Size') > 0, response.get('Contents')):
            key = photo.get('Key')
            thumbnail = f"https://s3.ap-northeast-2.amazonaws.com/{bucket}/{key}"

            photos.append({
                'thumbnail': thumbnail,
                'url': thumbnail.replace('/thumbnails', '')
            })

        groups.append({
            'name': name,
            'prefix': prefix,
            'photos': photos
        })

    context = {
        'groups': groups
    }

    return render_template('main.html', context=context)


@atexit.register
def bye():
    cursor.close()
    conn.close()


if __name__ == '__main__':
    app.secret_key = os.environ['GALLERY_SECRET_KEY']
    app.run(host='0.0.0.0')
