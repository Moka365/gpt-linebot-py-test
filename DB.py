import pymysql

class Database:
    def __init__(self, host, port, user, password, db, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.charset = charset
        self.cursorclass = cursorclass
        self.conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            charset=self.charset,
            cursorclass=self.cursorclass
        )
        self.cursor = self.conn.cursor()

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params)

    def fetchall(self):
        return self.cursor.fetchall()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()