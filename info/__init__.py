from flask import Flask
from flask.ext.session import Session
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import CSRFProtect
from redis import StrictRedis

from config import config

db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config[config_name])
    # 初始化数据库
    db.init_app(app)
    # 初始化redis存储对象
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST, port=config["development"].REDIS_PORT)
    # 开启当前项目 CSRF 保护, 只做服务器验证功能
    CSRFProtect(app)
    # 设置session保存位置
    Session(app)

    return app
