from flask import Flask, session
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import CSRFProtect
from redis import StrictRedis
# 可以用来指定 session 保存的位置
from flask_session import Session


class Config(object):
    """项目的配置"""
    DEBUG = True

    SECRET_KEY = "hu112LK9YAvRZMO++1XCsl2oZ05DFCROrbByeugLeNbvX1Fw1jZwaB6YCwdWW3jR"

    """为MySQL数据库添加配置"""
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/information27"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis的配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # Session的配置
    SESSION_TYPE = "redis"
    # 设置需要签名
    SESSION_USE_SIGNER = True
    # 指定SESSION保存的redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 设置需要过期
    SESSION_PERMANENT = False
    # 设置过期时间
    PERMANENT_SESSION_LIFETIME = 86400 * 2


app = Flask(__name__)
# 加载配置
app.config.from_object(Config)
# 初始化数据库
db = SQLAlchemy(app)
# 初始化redis存储对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
# 开启当前项目 CSRF 保护, 只做服务器验证功能
CSRFProtect(app)
# 设置session保存位置
Session(app)

manager = Manager(app)
# 将app和db关联
Migrate(app, db)
# 将迁移命令添加到manager中
manager.add_command('db', MigrateCommand)


@app.route('/')
def index():
    session["name"] = "itheima"
    return 'Hello Index!'


if __name__ == '__main__':
    manager.run()