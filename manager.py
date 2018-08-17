from flask import current_app
import logging
from flask import session
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager

from info import create_app, db

# 通过指定的配置名字创建对应配置的app
app = create_app('development')

manager = Manager(app)
# 将app和db关联
Migrate(app, db)
# 将迁移命令添加到manager中
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
