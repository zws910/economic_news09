# 管理员登录页面的蓝图


from flask import Blueprint

admin_blu = Blueprint("admin", __name__, url_prefix='/admin')

from . import views
