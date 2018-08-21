import random
import re
from datetime import datetime

from flask import abort, jsonify
from flask import current_app
from flask import make_response
from flask import request
from flask import session

from info import constants, db
from info import redis_store
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blu


@passport_blu.route('/logout')
def logout():
    """
    退出登录
    :return:
    """
    # pop是移除session中的数据(dict)
    # pop 会有一个返回值, 如果要移除的key不存在, 就返回None
    session.pop('user_id', None)
    session.pop('mobile', None)
    session.pop('nick_name', None)

    return jsonify(errno=RET.OK, errmsg="退出成功")


@passport_blu.route('/login', methods=["POST"])
def login():
    """
    登录
    1. 获取参数
    2. 校验参数
    3. 校验密码是否正确
    4. 保存用户的登陆状态
    5. 响应OK
    :return:
    """
    # 1 获取参数
    params_dict = request.json
    mobile = params_dict.get("mobile")
    password = params_dict.get("password")

    # 2 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 校验手机号是否正确
    if not re.match(r'1[35678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 3 校验密码是否正确
    # 先查询当前是否有指定手机号的用户
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")
    # 校验登陆的密码和当前用户的密码是否一致
    if not user.check_passowrd(password):
        return jsonify(errno=RET.PWDERR, errmsg="用户名或密码错误")

    # 4. 保存用户的登陆状态
    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    # 设置当前用户最后一次登录的时间
    user.last_login = datetime.now()

    # try:
    #     db.session.commit()
    # except Exception as e:
    #     db.session.rollback()
    #     current_app.logger.error(e)

    # 5.
    return jsonify(errno=RET.OK, errmsg="登录成功")


@passport_blu.route('/register', methods=['POST'])
def register():
    """
    注册的逻辑
    1. 获取参数
    2. 校验参数
    3. 取到服务器保存的真实的短信验证码内容
    4. 校验用户输入的短信验证码内容和真实验证码内容是否一直
    5. 如果一致, 初始化USER模型
    6. 将user模型添加数据库
    7. 返回响应
    :return:
    """
    # 1. 获取参数
    param_dict = request.json
    mobile = param_dict.get("mobile")
    smscode = param_dict.get("smscode")
    password = param_dict.get("password")

    # 2. 校验参数
    if not all([mobile, smscode, password]):
        return
    # 校验手机号是否正确
    if not re.match(r'1[35678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 3
    try:
        real_sms_code = redis_store.get("SMS_" + mobile)
        print(real_sms_code)  # for test
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="数据查询失败")

    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg="验证码过期")

    # 4
    if real_sms_code != smscode:
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")

    # 5 如果一致, 初始化User模型, 并且赋值属性
    user = User()
    user.mobile = mobile
    # 暂时没有昵称, 使用手机号代替
    user.nick_name = mobile
    # 记录用户最后一次登陆时间
    user.last_login = datetime.now()
    # TODO 对密码做处理
    user.password = password
    # 6 添加到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

    # 往session中保存数据表示当前已经登陆
    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    # 7 返回OK响应
    return jsonify(errno=RET.OK, errmsg="注册成功")


@passport_blu.route('/sms_code', methods=['POST'])
def send_sms_code():
    """
    发送短信验证码
    1. 获取参数: 手机号, 图片验证码内容, 图片验证码的随机编号
    2. 校验参数(参数是否符合规则, 判断是否有值)
    3. 先从redis中取出真实的验证码内容
    4. 与用户的验证码内容进行对比, 如果对比不一致, 那么返回验证码输入错误
    5. 如果一致, 生成验证码的内容(随机数据)
    6. 发送短信验证码
    7. 告知发送结果
    """

    # return jsonify(errno=RET.OK, errmsg="发送成功")

    # 1. 获取参数
    # '{"mobile": "18611111111"}, "image_code": "AAAA", "image_code_id": d1f32a132a1f3s1a'
    # params_dict = json.loads(request.data)
    params_dict = request.json

    mobile = params_dict.get("mobile")
    image_code = params_dict.get("image_code")
    image_code_id = params_dict.get("image_code_id")

    # 2. 校验参数
    if not all([mobile, image_code, image_code_id]):
        # jsonify返回一个json字符串  {"errno": "RET.PARAMERR", "errmsg": "参数有误"}
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    if not re.match(r'1[35678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 3.
    try:
        real_image_code = redis_store.get("ImageCodeId_" + image_code_id)
        print(real_image_code)  # for test
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码已过期")

    # 4.
    if real_image_code.upper() != image_code.upper():
        print("---->real: %s     code: %s" % (real_image_code, image_code))  # for test
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码输入错误")

    # 5.
    # 随机数字, 保证数字长度为6位, 不够在前面补上0
    sms_code_str = "%06d" % random.randint(0, 999999)
    current_app.logger.debug("短信验证码内容是: %s" % sms_code_str)

    # 6. 发送短信验证码
    # result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES], "1")
    # if result != 0:
    #     # 代表发送不成功
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送短信失败")

    # 保存验证码内容到redis
    try:
        redis_store.set('SMS_' + mobile, sms_code_str)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")

    return jsonify(errno=RET.OK, errmsg="发送成功")


@passport_blu.route('/image_code')
def get_image_code():
    """
    生成图片验证码并返回"
    1. 取到参数
    2. 判断参数是否有值
    3. 生成图片验证码
    4. 保存图片验证码文字内容到redis
    5. 返回验证码图片
    """
    # 1. 取到参数
    # args: 取到url中 ? 后面的参数
    image_code_id = request.args.get("imageCodeId", None)
    # 2. 判断参数是否有值
    if not image_code_id:
        return abort(403)

    # 3. 生成图片验证码
    name, text, image = captcha.generate_captcha()

    # 4. 保存图片验证码文字内容到redis
    try:
        redis_store.setex("ImageCodeId_" + image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)

    # 5. 返回验证码图片
    response = make_response(image)
    current_app.logger.debug(text)
    # 设置数据的类型, 以便浏览器更加智能识别其是什么类型
    response.headers["Content-Type"] = "image/jpg"
    return response
