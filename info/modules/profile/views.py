from flask import abort
from flask import current_app
from flask import g, jsonify
from flask import redirect
from flask import render_template
from flask import request

from info import constants, db
from info.constants import QINIU_DOMIN_PREFIX
from info.models import Category, News, User
from info.modules.profile import profile_blu
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET


@profile_blu.route('/other_news_list')
def other_news_list():
    """返回指定用户发布的新闻"""

    other_id = request.args.get("user_id")
    page = request.args.get("p", 1)

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        other = User.query.get(other_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not other:
        return jsonify(errno=RET.NODATA, errmsg="当前用户不存在")

    try:
        paginate = other.news_list.paginate(page, constants.OTHER_NEWS_PAGE_MAX_COUNT, False)
        news_li = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    news_dict_li = []

    for news_item in news_li:
        news_dict_li.append(news_item.to_basic_dict())

    data = {
        "news_list": news_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }

    return jsonify(errno=RET.OK, errmsg="OK", data=data)


@profile_blu.route('/other_info')
@user_login_data
def other_info():
    user = g.user
    # 去查询其他人的用户信息
    other_id = request.args.get("user_id")

    if not other_id:
        abort(404)

    # 查询指定id的用户信息
    try:
        other = User.query.get(other_id)
    except Exception as e:
        current_app.logger.error(e)

    if not other:
        abort(404)

    is_followed = False
    # 如果当前新闻有作者, 并且当前登录用户已关注过这个用户
    if other and user:
        if other in user.followed:
            is_followed = True

    data = {
        "user": g.user.to_dict() if g.user else None,
        "other_info": other.to_dict(),
        "is_followed": is_followed
    }
    return render_template('news/other.html', data=data)


@profile_blu.route('/user_follow')
@user_login_data
def user_follow():
    # 获取参数
    page = request.args.get("p", 1)
    # 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 查询用户指定页数的收藏的新闻

    user = g.user
    followers = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.followed.paginate(page, constants.USER_FOLLOWED_MAX_COUNT, False)
        current_page = paginate.page
        total_page = paginate.pages
        followers = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    users_dict_li = []
    for follower in followers:
        users_dict_li.append(follower.to_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "users": users_dict_li
    }

    return render_template('news/user_follow.html', data=data)


@profile_blu.route('/news_list')
@user_login_data
def user_news_list():
    user = g.user

    page = request.args.get("p", 1)

    news_list = []
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news in news_list:
        news_dict_li.append(news.to_review_dict())

    data = {
        "news_list": news_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }

    return render_template('news/user_news_list.html', data=data)


@profile_blu.route('/news_release', methods=["GET", "POST"])
@user_login_data
def news_release():
    """新闻发布"""
    if request.method == "GET":
        categories = []
        # 加载新闻分类数据
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)

        category_dict_li = []
        for category in categories:
            category_dict_li.append(category.to_dict())

        # 移除 最新 的分类
        category_dict_li.pop(0)

        data = {
            "categories": category_dict_li
        }

        return render_template('news/user_news_release.html', data=data)

    # 1. 获取要提交的数据
    title = request.form.get("title")  # 标题
    source = "个人发布"  # 新闻来源
    digest = request.form.get("digest")  # 摘要
    content = request.form.get("content")  # 新闻内容
    index_image = request.files.get("index_image")  # 索引图片
    category_id = request.form.get("category_id")  # 分类id
    # 2. 校验参数
    # 2.1判断数据是否有值
    if not all([title, source, digest, content, index_image, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 2.2
    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 3. 取到图片, 将图片上传到七牛云
    try:
        index_image_data = index_image.read()
        key = storage(index_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 初始化模型并设置数据
    news = News()
    news.title = title
    news.digest = digest
    news.source = source
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.category_id = category_id
    news.user_id = g.user.id
    # 审核状态
    news.status = 1

    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

    return jsonify(errno=RET.OK, errmsg="发布成功!")


@profile_blu.route('/collection')
@user_login_data
def user_collection():
    # 获取参数
    page = request.args.get("p", 1)
    # 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 查询用户指定页数的收藏的新闻

    user = g.user
    news_list = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        current_page = paginate.page
        total_page = paginate.pages
        news_list = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news in news_list:
        news_dict_li.append(news.to_basic_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "collections": news_dict_li
    }

    return render_template('news/user_collection.html', data=data)


@profile_blu.route('/pass_info', methods=["GET", "POST"])
@user_login_data
def pass_info():
    if request.method == "GET":
        return render_template("news/user_pass_info.html", data={"user": g.user.to_dict()})

    # 1. 获取参数
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    # 2. 校验参数
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 判断旧密码是否正确
    user = g.user
    if not user.check_passowrd(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="原密码错误")

    # 4. 设置新密码
    user.password = new_password

    return jsonify(errno=RET.OK, errmsg="保存成功")


@profile_blu.route('/pic_info', methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user

    if request.method == "GET":
        return render_template("news/user_pic_info.html", data={"user": g.user.to_dict()})

    # 如果是POST表示修改头像
    # 1. 取到上传的图片
    try:
        avatar = request.files.get("avatar").read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 使用自己封装的storage方法进行图片上传
        key = storage(avatar)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传头像失败")

    # 3. 保存头像地址
    user.avatar_url = key

    return jsonify(errno=RET.OK, errmsg="OK", data={"avatar_url": QINIU_DOMIN_PREFIX + key})


@profile_blu.route('/base_info', methods=["GET", "POST"])
@user_login_data
def base_info():
    # 不同的请求参数做不同的事情
    if request.method == "GET":
        return render_template('news/user_base_info.html', data={"user": g.user.to_dict()})

    # 代表是修改用户数据
    # 1. 取到传入的参数
    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    # 2. 校验参数
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if gender not in ("MAN", "WOMAN"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    user = g.user
    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender

    return jsonify(errno=RET.OK, errmsg="OK")


@profile_blu.route('/info')
@user_login_data
def user_info():
    user = g.user

    if not user:
        return redirect("/")

    data = {"user": user.to_dict()}

    return render_template('news/user.html', data=data)
