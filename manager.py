from flask import session
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager

from info import app, db

manager = Manager(app)
# 将app和db关联
Migrate(app, db)
# 将迁移命令添加到manager中
manager.add_command('db', MigrateCommand)


@app.route('/')
def index():
    session["name"] = "itheima"
    return 'Hello Index222!'


if __name__ == '__main__':
    manager.run()
