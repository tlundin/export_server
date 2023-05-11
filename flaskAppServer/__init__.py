import os, logging

from flask import Flask

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__,instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY='dev')
    # app.config['UPLOAD_FOLDER'] = IMG_UPLOAD_FOLDER
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from flaskAppServer import export_api, auth
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    # apply the blueprints to the app
    app.register_blueprint(auth.bp)
    app.register_blueprint(export_api.bp)
    return app
