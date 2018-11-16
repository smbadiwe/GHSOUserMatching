import psycopg2 as psql


class DbConnection(object):
    """
     Abstraction for database connections
    """
    __con = None
    __cur = None

    def dbConnection(self):
        return self

    def create(self, db_name="gh_so"):
        self.__con = psql.connect('dbname={}'.format(db_name))
        self.__cur = self.__con.cursor()

    def executeScript(self, sqlScript, queryParams=None):
        if queryParams is None:
            self.__cur.execute(sqlScript)
        else:
            self.__cur.execute(sqlScript, queryParams)

    def fetchData(self, sqlSelectScript, queryParams=None):
        self.executeScript(sqlSelectScript, queryParams)
        return self.__cur.fetchall()

    def commit(self):
        self.__con.commit()

    def close(self):
        self.__con.commit()
        self.__cur.close()
        self.__con.close()
