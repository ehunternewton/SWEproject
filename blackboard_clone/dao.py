from flask_mysqldb import MySQL
from flask import flash


class dao:
    mysql=None;

    def connect_db(app):
        mysql = MySQL(app)
        app.config['MYSQL_HOST'] = 'xmenbb.c4dthivni7sx.us-east-1.rds.amazonaws.com'
        app.config['MYSQL_USER'] = 'root'
        app.config['MYSQL_PASSWORD'] = '12345678'
        app.config['MYSQL_DB'] = 'myflaskapp'
        app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
        dao.mysql = mysql
        return mysql;

    @staticmethod
    def execute(sqlstatement, values, fetch):
        cur = dao.mysql.connection.cursor()
        result = cur.execute(sqlstatement, values)

        if fetch=='one':
            data = cur.fetchone()
        elif fetch == 'all':
            data = cur.fetchall()
        elif fetch == 'commit':
            # Commit to DB
            data = dao.mysql.connection.commit()
        else:
            data = cur.fetchall()

        cur.close()

        return [result, data]

