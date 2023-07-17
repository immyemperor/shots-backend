import json
import boto3
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import uuid
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.sqlite3'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)

error_obj = {}
error_obj['msg'] = 'Internal Server Error'
error_obj['code'] = 500

def generateUUID():
    return uuid.uuid4().hex


class FileUploads(db.Model):
    id = db.Column('file_id', generateUUID(), primary_key = True)
    filename = db.Column(db.String(100))
    object_url = db.Column(db.String(2000))
    user_id = db.Column(db.String(200))
    key = db.Column(db.String(200)) 
    date = db.Column(db.String(10))

def __init__(self, filename, object_url, user_id, key, date):
    self.filename = filename
    self.object_url = object_url
    self.user_id = user_id
    self.key = key
    self.date = date

class Shots(db.Model):
    id = db.Column('shot_id', generateUUID(), primary_key = True)
    video_object_url = db.Column(db.String(2000))
    thumbnail_object_url = db.Column(db.String(2000))
    user_id = db.Column(db.String(200))
    description = db.Column(db.String(10000))
    title = db.Column(db.String(10))
    is_private = db.Column(db.String(10))
    comments = db.Column(db.String(10000))
    shared = db.Column(db.String(10000))
    views = db.Column(db.String(10000))
    date_added = db.Column(db.String(10))
    date_updated = db.Column(db.String(10))

def __init__(self, 
             video_object_url, 
             thumbnail_object_url,
               user_id, 
               description, 
               title,
               is_private,
               comments,
               shared,
               views,
               date_added,
               date_updated):
    self.video_object_url = video_object_url
    self.thumbnail_object_url = thumbnail_object_url
    self.user_id = user_id
    self.description = description
    self.title = title
    self.is_private = is_private
    self.comments = comments
    self.shared = shared
    self.views = views
    self.date_added = date_added
    self.date_updated = date_updated

@app.route("/api/v1/uploadVideo", methods=["POST"])
def uploadVideo():
    
    # Get the video file from the request.
    try: 
        video_file = request.files["video_file"]
        user_id = generateUUID()
        print("req: ",request.files)
        # Upload the video file to the S3 bucket.
        s3 = boto3.resource("s3",aws_access_key_id='AKIAS74JVX2LRWRGHXKK',
            aws_secret_access_key= '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')
        bucket = "success-shots-bucket"
        file = video_file.filename
        ext = file.split('.')[-1]
        key = generateUUID()
        filename = str(user_id)+"#"+key+ext
        s3.Object(bucket, f'videos/{filename}').put(Body=video_file.read())
        
        file_url = f'https://{bucket}.s3.ap-south-1.amazonaws.com/videos/{filename}'
        response = {}
        file_data = FileUploads(
            object_url = file_url,
            key = key,
            user_id = user_id,
            filename = key,
            date = datetime.datetime.now()
            )

        db.session.add(file_data)
        db.session.commit()
        response['object_url'] = file_url
        response['key'] = key
        response['user_id'] = user_id
        response['filename'] = filename
        return response
    except Exception as error:
        print(error)
        return  error_obj

@app.route("/api/v1/uploadImage", methods=["POST"])
def uploadImage():
    # Get the image file from the request.
    image_file = request.files["image_file"]

    # Upload the image file to the S3 bucket.
    s3 = boto3.resource("s3")
    bucket = "my-bucket"
   
    #s3.Object(bucket, key).put(Body=json.dumps(image_file.read()))

    return "Image uploaded successfully!"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True, port=8080)
