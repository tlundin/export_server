from flask import Blueprint
import logging

bp = Blueprint('export_api',__name__,url_prefix='/')


@bp.route('/greeting')
def greeting():
    logging.info('GET /greeting')
    return 'Hello this message is coming from query Blueprint.'

IMG_UPLOAD_FOLDER = '/home/ec2-user/flask/export/images'
FILE_UPLOAD_FOLDER = '/home/ec2-user/flask/export/files'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'json'}


@bp.route('/upload', methods=['POST'])
def upload_img():
    logging.info('GET /upload')
    if request.method == 'POST':
        for filename in request.files:
            if allowed_file(filename):
                file = request.files[filename]
                print("name", file.filename)
                print("type", file.content_type)
                print("size", file.content_length)
                if file.content_type.startswith("image"):
                    file.save(IMG_UPLOAD_FOLDER + "/" + filename)
                else:
                    file.save(FILE_UPLOAD_FOLDER + "/" + filename)
                return Response("OK")
            else:
                return Response('filename {} is not allowed'.format(filename), 403)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/files",methods=['GET'])
def _list_files():
    logging.info('GET /files')
    return list_files(FILE_UPLOAD_FOLDER)


@bp.route("/images",methods=['GET'])
def list_files(folder=IMG_UPLOAD_FOLDER):
    logging.info('GET /images')
    from os import listdir
    from os.path import isfile, join
    onlyfiles = [f for f in listdir(folder) if isfile(join(folder, f))]
    return str(onlyfiles)


@bp.route("/files/<path:name>")
def download_file(name):
    logging.info('GET /files/{}'.format(name))
    return send_from_directory(
        FILE_UPLOAD_FOLDER, name, as_attachment=True
    )


@bp.route("/images/<path:name>")
def download_image(name):
    logging.info('GET /images/{}'.format(name))
    return send_from_directory(
        IMG_UPLOAD_FOLDER, name, as_attachment=True
    )

