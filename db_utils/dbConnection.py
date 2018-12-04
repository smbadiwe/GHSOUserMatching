import psycopg2 as psql
import yaml


def getDbConfig():
    with open("../config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg




class DbConnection(object):
    """
     Abstraction for database connections
    """
    __con = None
    __cur = None

    def DbConnection(self):
        return self

    def create(self):
        print("Creating DbConnection")
        con, cur = getDbConfig()

        # self.__con = psql.connect(database=cfg['database'], user=cfg['user'], host=cfg['host'], port=cfg['port'], password=cfg['password'])
        connStr = "dbname={} user={} password={} host={} port={}"\
            .format(cfg['database'], cfg['user'], cfg['password'], cfg['host'], cfg['port'])
        self.__con = psql.connect(connStr)
        self.__cur = self.__con.cursor()
        print("Created DbConnection. {}".format(connStr))

    def executeScript(self, sqlScript, queryParams=None):
        print("Executing script")
        if queryParams is None:
            self.__cur.execute(sqlScript)
        else:
            self.__cur.execute(sqlScript, queryParams)
        print("Done executing script")

    def fetchData(self, sqlSelectScript, queryParams=None):
        print("Executing SELECT script")
        self.executeScript(sqlSelectScript, queryParams)
        return self.__cur.fetchall()

    def commit(self):
        print("Committing DbConnection")
        self.__con.commit()

    def close(self):
        print("Closing DbConnection")
        self.__con.commit()
        self.__cur.close()
        self.__con.close()
        print("Closed DbConnection")
