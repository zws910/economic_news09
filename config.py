from flask import logging
from redis import StrictRedis


class Config(object):
    """项目的配置"""

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

    # 设置日志等级
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """开发环境下的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境下的配置"""
    DEBUG = False


class TestingConfig(Config):
    """单元测试环境下的配置"""
    DEBUG = True
    TESTING = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}

