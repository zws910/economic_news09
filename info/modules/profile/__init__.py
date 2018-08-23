# 用户档案的相关业务逻辑

from flask import Blueprint

profile_blu = Blueprint("profile", __name__, url_prefix="/user")

from . import views
