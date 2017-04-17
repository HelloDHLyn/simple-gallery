import atexit
import psycopg2

from flask import Flask, render_template
from config.db import *

app = Flask(__name__)
conn = psycopg2.connect(host=DB_HOST, dbname=DB_DATABASE, user=DB_USERNAME, password=DB_PASSWORD)
cursor = conn.cursor()


@app.route("/")
def hello():
    """
    로그인 화면.
    :return:
    """

    return "Hello, flask!"


@app.route("/main")
def main():
    """
    메인 화면.
    :return:
    """
    # 사진 그룹을 불러온다.
    cursor.execute("SELECT * FROM gallery_photo_group")

    import boto3

    groups = []
    for name, bucket, prefix in cursor.fetchall():
        client = boto3.client("s3")
        response = client.list_objects(Bucket=bucket, Prefix=f"{prefix}/thumbnails")

        urls = []
        for photo in response.get("Contents"):
            if photo.get("Size") == 0:
                continue

            key = photo.get("Key")
            urls.append(f"https://s3.ap-northeast-2.amazonaws.com/{bucket}/{key}")

        groups.append({'name': name, 'urls': urls})

    context = {
        'groups': groups
    }

    return render_template("main.html", context=context)


@atexit.register
def bye():
    cursor.close()
    conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0")
