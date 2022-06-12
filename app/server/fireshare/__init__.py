import os
import os.path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from pathlib import Path
import logging
import json
import secrets

logger = logging.getLogger('fireshare')
handler = logging.StreamHandler()
handler.setLevel(os.getenv('FS_LOGLEVEL', 'INFO').upper())
formatter = logging.Formatter('%(asctime)s %(levelname)-7s %(module)s.%(funcName)s:%(lineno)d | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()
migrate = Migrate()

def create_app(init_schedule=False):
    app = Flask(__name__, static_url_path='', static_folder='build', template_folder='build')
    CORS(app, supports_credentials=True)
    if 'DATA_DIRECTORY' not in os.environ:
        raise Exception("DATA_DIRECTORY not found in environment")

    app.config['ENVIRONMENT'] = os.getenv('ENVIRONMENT')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32)) 
    app.config['DATA_DIRECTORY'] = os.getenv('DATA_DIRECTORY')
    app.config['VIDEO_DIRECTORY'] = os.getenv('VIDEO_DIRECTORY')
    app.config['PROCESSED_DIRECTORY'] = os.getenv('PROCESSED_DIRECTORY')
    app.config['ADMIN_PASSWORD'] = os.getenv('ADMIN_PASSWORD')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{app.config["DATA_DIRECTORY"]}/db.sqlite'
    app.config['SCHEDULED_JOBS_DATABASE_URI'] = f'sqlite:///jobs.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['INIT_SCHEDULE'] = init_schedule
    app.config['MINUTES_BETWEEN_VIDEO_SCANS'] = int(os.getenv('MINUTES_BETWEEN_VIDEO_SCANS', '5'))

    paths = {
        'data': Path(app.config['DATA_DIRECTORY']),
        'video': Path(app.config['VIDEO_DIRECTORY']),
        'processed': Path(app.config['PROCESSED_DIRECTORY']),
    }
    app.config['PATHS'] = paths
    for k, path in paths.items():
        if not path.is_dir():
            logger.info(f"Creating {k} directory at {str(path)}")
            path.mkdir(parents=True, exist_ok=True)
    subpaths = [
        paths['processed'] / 'video_links',
        paths['processed'] / 'derived',
    ]
    for subpath in subpaths:
        if not subpath.is_dir():
            logger.info(f"Creating subpath directory at {str(subpath.absolute())}")
            subpath.mkdir(parents=True, exist_ok=True)
    ui_config = paths['data'] / 'ui-config.json'
    if not ui_config.exists():
        default_ui_config = {}
        ui_config.write_text(json.dumps(default_ui_config, indent=2))

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for api routes
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    if init_schedule:
        from .schedule import init_schedule
        init_schedule(app.config['SCHEDULED_JOBS_DATABASE_URI'],
            app.config['MINUTES_BETWEEN_VIDEO_SCANS'])

    with app.app_context():
        # db.create_all()
        return app