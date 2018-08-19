# 登陆注册的相关业务逻辑都放在当前模块


from flask import Blueprint

passport_blu = Blueprint("passport_blu", __name__, url_prefix='/passport')

from . import views
