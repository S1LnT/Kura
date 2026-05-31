from gevent import monkey; monkey.patch_all()
import os,shutil
from werkzeug.middleware.proxy_fix import ProxyFix
from . import customjinjafuncs
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required, current_user, login_required, logout_user, LoginManager
from flask_bcrypt import Bcrypt 
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO, emit
import logging
from flask_dropzone import Dropzone
import configparser

log_file_path = '/home/dietpi/kura/logs/debug.log'
logging.basicConfig(filename=log_file_path, level=logging.DEBUG,filemode="w",
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
dropzone = Dropzone()
db = SQLAlchemy()
lm = LoginManager()
bc = Bcrypt()
csrf = CSRFProtect()
socketio = SocketIO()

class AppConfig:
    #General config
    APP_VERSION = "0.0.1"
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data.json"))
    PERM_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "permission_levels.json"))
    # Notes page config
    NOTES_INSTANCES_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "/home/dietpi/kura/notes/notes_instances"))
    NOTES_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "/home/dietpi/kura/notes/notes_data.json"))
    # Post page config
    POSTS_PER_PAGE = 3
    UPLOAD_FOLDER_REL = "/mnt/Kuras/Alpha/"
    TEMP_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "/mnt/Kuras/tmp/"))
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), UPLOAD_FOLDER_REL))
    # Admin page config
    DISK_BUFFER_SIZE = 1 * 1024 * 1024 * 1024

appConfig = AppConfig() 

def page_not_found(e):
  return render_template('404.html'), 404

def reset_tmp():
    try:
        if os.path.isdir(appConfig.TEMP_FOLDER):
            shutil.rmtree(appConfig.TEMP_FOLDER)
        if not os.path.isdir(appConfig.TEMP_FOLDER):
            os.makedirs(appConfig.TEMP_FOLDER)
    except Exception as e:
        logger.error(f"Error resetting temp folder:{e}")

reset_tmp()
def create_app():
    logger.info("App starting up")
    app = Flask(__name__)
    app.register_error_handler(404, page_not_found)
    app.secret_key = '275bb7f695e55130beac0efdcabe0ac3da6ea69553d5e711ae3915465492b5b6'
    app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///database.db'
    app.config['DROPZONE_ENABLE_CSRF'] = True
    app.app_context().push()
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    dropzone.init_app(app)
    app.jinja_env.globals.update(do=customjinjafuncs.do)
    db.init_app(app)
    bc.init_app(app)
    lm.init_app(app)
    socketio.init_app(app,async_mode='gevent', message_queue='redis://')
    csrf.init_app(app)
    logger.info("App initialized")
    lm.login_view = 'auth.login'

    from .views.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .views.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from .views.notes import notes as notes_blueprint
    app.register_blueprint(notes_blueprint)

    from .views.home import home as home_blueprint
    app.register_blueprint(home_blueprint)
    
    from .views.post import post as post_blueprint
    app.register_blueprint(post_blueprint)

    return app
