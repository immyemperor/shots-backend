import json
import boto3
from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
import uuid
import datetime
import logging
from sqlalchemy import JSON
from flask import jsonify

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.sqlite3'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)
logging.basicConfig(level=logging.DEBUG, format=f'[Success-Shot] %(asctime)s %(levelname)s %(name)s : %(message)s')
log = app.logger
error_obj = {}
error_obj['msg'] = 'Internal Server Error'
error_obj['code'] = 500

def generateUUID():
    return uuid.uuid4().hex


class FileUploads(db.Model):
    id = db.Column('file_id', db.Integer, primary_key = True)
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
    id = db.Column('shot_id', db.Integer, primary_key = True)
    video_object_url = db.Column(db.String(2000))
    thumbnail_object_url = db.Column(db.String(2000))
    user_id = db.Column(db.String(200))
    description = db.Column(db.String(10000))
    title = db.Column(db.String(10))
    is_private = db.Column(db.String(10))
    comments = db.Column(JSON)
    shared = db.Column(JSON)
    total_views = db.Column(db.Integer)
    views = db.Column(JSON)
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
                total_views,
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
        self.tatal_views = total_views

    def to_json(self):
        data = {}
        data["shot_id"]: self.id
        data["video_object_url"]= self.video_object_url
        data["thumbnail_object_url"]= self.thumbnail_object_url
        data["user_id"]=  self.user_id
        data["description"]=  self.description
        data["title"]=  self.title
        data["is_private"]=  self.is_private
        data["comments"] =  self.comments
        data["shared"] = self.shared
        data["views"] =  self.views
        data["tatal_views"] =  self.tatal_views
        data["date_added"]=  self.date_added
        data["date_updated"] =  self.date_updated
        # return {
        #     "shot_id": self.id,
        #     "video_object_url": self.video_object_url,
        #     "thumbnail_object_url": self.thumbnail_object_url,
        #     "user_id":  self.user_id,
        #     "description":  self.description,
        #     "title" :  self.title,
        #     "is_private":  self.is_private,
        #     "comments" :  self.comments,
        #     "shared" : self.shared,
        #     "views" :  self.views,
        #     "date_added":  self.date_added,
        #     "date_updated" :  self.date_updated   
        # }
        return data


@app.route("/api/v1/addShot", methods=["POST"])
def addShot():
    
    # Get the video file from the request.
    try: 
        log.info('Fetching Request')
        video_file = request.files["video_file"]
        if(video_file):
            log.info('Video file found')
        image_file = request.files["image_file"]
        if(video_file):
            log.info('Image file found')
        title = request.form["title"]
        description = request.form["description"]
        is_private = request.form["is_private"]
        user_id = request.form["user_id"]
        print("req: ",request.files)
        # Upload the video file to the S3 bucket.
        log.info('Trying to log-in into AWS Bucket')
        s3 = boto3.resource("s3",aws_access_key_id='AKIAS74JVX2LRWRGHXKK',
            aws_secret_access_key= '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')
        bucket = "success-shots-bucket"
        if s3:
            log.info('Connecte AWS Bucket: '+ bucket)
       
        v_file = video_file.filename
        v_ext = v_file.split('.')[-1]
        key = generateUUID()
        v_filename = str(user_id) + "#" + key + '.' + v_ext
        log.info('Pushing to video file into AWS Bucket: '+ bucket)
        s3.Object(bucket, f'videos/{v_filename}').put(Body=video_file.read())
        log.info('Video file pushed into AWS Bucket: '+ bucket)
        v_file_url = f'https://{bucket}.s3.ap-south-1.amazonaws.com/videos/{v_filename}'
        log.info('Adding file info to database')
        file_data = FileUploads(
            object_url = v_file_url,
            key = key,
            user_id = user_id,
            filename = v_filename,
            date = datetime.datetime.now()
            )
        db.session.add(file_data)
        db.session.commit()
        log.info('FIle info saved to database')
        i_file = image_file.filename
        i_ext = i_file.split('.')[-1]
        i_filename = str(user_id) + "#" + key + '.' +i_ext
        log.info('Pushing to image file into AWS Bucket: '+ bucket)
        s3.Object(bucket, f'videos/{v_filename}').put(Body=video_file.read())
        log.info('Image file pushed into AWS Bucket: '+ bucket)
        image_file_url = f'https://{bucket}.s3.ap-south-1.amazonaws.com/thumbnails/{i_filename}'
        log.info('Adding image file info to database')
        i_file_data = FileUploads(
            object_url = image_file_url,
            key = key,
            user_id = user_id,
            filename = i_filename,
            date = datetime.datetime.now()
            )
        db.session.add(i_file_data)
        db.session.commit()
        log.info('FIle info saved to database')
        log.info('Preparing Shot to be added')
        add_shot = Shots(
            video_object_url = v_file_url,
            thumbnail_object_url = image_file_url,
            user_id = user_id,
            description = description,
            title = title,
            is_private = is_private,
            comments = {'comments_mutual':[],'comments':[]},
            shared = {'shared_mutual':[],'shared':[]},
            views = 0,
            date_added = datetime.datetime.now(),
            date_updated = datetime.datetime.now(),
        )
        db.session.add(add_shot)
        db.session.commit()
        log.info('Shot added to DB')
        log.info('Preparing Response...')
        log.info('Fetching saved data from DB')
        latest = Shots.query.filter_by(user_id = user_id).first()
        response = {}
        response['data'] = [obj.to_json() for obj in latest]
        return jsonify(response), 201
    except Exception as error:
        print(error)
        log.info('Exception occured: ',error)
        return  jsonify(error_obj), 500

@app.route("/api/v1/getAllShot/<user_id>", methods=["GET"])
def getAllShots(user_id):
    try:
        latest = Shots.query.filter_by(user_id = user_id).all()
        response = {}
        response['data'] = [obj.to_json() for obj in latest]
        response['status'] = 201
        return jsonify(response), 201
    except Exception as error:
        print(error)
        log.info('Exception occured: ',error)
        error_obj['msg'] ="404 Not Found"
        response['status'] = 404
        return  jsonify(error_obj), 404


@app.route("/api/v1/share/<shot_id>", methods=["POST"])
def shareShots(shot_id):
    try:
        user_id = request.form["user_id"]
        shot = Shots.query.filter_by(shot_id = shot_id).first()
        shot.shared = list(shot.shared).append({"user_id": user_id})
        db.session.commit()
        response = {}
        response['message'] = "Shared successfully"
        response['status'] = 200
        return jsonify(response), 200
    except Exception as error:
        print(error)
        log.info('Exception occured: ',error)
        error_obj['msg'] ="404 Not Found"
        return  jsonify(error_obj), 404
    
@app.route("/api/v1/view/<shot_id>", methods=["POST"])
def viewShots(shot_id):
    try:
        user_id = request.form["user_id"]
        shot = Shots.query.filter_by(shot_id = shot_id).first()
        shot.views = list(shot.views).append({"user_id": user_id})
        db.session.commit()
        response = {}
        response['message'] = "Shared successfully"
        response['status'] = 200
        return jsonify(response), 200
    except Exception as error:
        print(error)
        log.info('Exception occured: ',error)
        error_obj['msg'] ="404 Not Found"
        return  jsonify(error_obj), 404

@app.route("/api/v1/addComment/<shot_id>", methods=["POST"])
def addComment(shot_id):
    try:
        user_id = request.form["user_id"]
        comment = request.form["comment"]
        shot = Shots.query.filter_by(shot_id = shot_id).first()
        shot.comments = list(shot.views).append(
            {
                "user_id": user_id,
                "comment": comment,
                "comment_id": generateUUID()
            })
        db.session.commit()
        response = {}
        response['message'] = "Shared successfully"
        response['status'] = 200
        return jsonify(response), 200
    except Exception as error:
        print(error)
        log.info('Exception occured: ',error)
        error_obj['msg'] ="404 Not Found"
        return  jsonify(error_obj), 404

@app.route("/api/v1/getAllComment/<shot_id>", methods=["POST"])
def getAllComments(shot_id):
    try:
        user_id = request.form["user_id"]
        shot = Shots.query.filter_by(shot_id = shot_id).all()
        response = {}
        response['message'] = "Shared successfully"
        response['status'] = 200
        return jsonify(response), 200
    except Exception as error:
        print(error)
        log.info('Exception occured: ',error)
        error_obj['msg'] ="404 Not Found"
        return  jsonify(error_obj), 404

if __name__ == "__main__":
    with app.app_context():
        
        log.info('Creating DB Tables')
        db.create_all()
        app.run(debug=True, port=8080)

   