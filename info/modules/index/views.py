from flask import current_app
from flask import render_template
from flask import session

from info import redis_store
from info.models import User
from . import index_blu


@index_blu.route('/')
def index():
    """
    显示首页
    :return:
    """

    user_id = session.get("user_id", None)
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)


    data = {
        "user": user.to_dict() if user else None
    }


    return render_template('news/index.html', data=data)


# 网页标签的小图标, 用send_static_file()查找指定的静态文件
@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
