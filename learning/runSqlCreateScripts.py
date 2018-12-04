import psycopg2 as psql
from appUtils import getDbConfig


def runSqlScripts(train_size, test_size):
    print("\n===========\nRUNNING runSqlScripts()\n===========\n")
    cfg = getDbConfig()
    con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
    cur = con.cursor()

    print("Running createAllDatasetView.sql script")
    with open("../sqlscripts/createAllDatasetView.sql", 'r') as r:
        query = r.read()
    cur.execute(query)
    con.commit()

    print("Running createTables.sql script")
    with open("../sqlscripts/createTables.sql", 'r') as r:
        query = r.read()
    cur.execute(query)
    con.commit()

    print("Running user_project_dec_mapping.sql script")
    with open("../sqlscripts/user_project_dec_mapping.sql", 'r') as r:
        query = r.read()
    cur.execute(query)
    con.commit()

    print("Running createTrainAndTestDatasetView.sql script")
    with open("../sqlscripts/createTrainAndTestDatasetView.sql", 'r') as r:
        query = r.read()
    query = query.replace("<train_size>", str(train_size // 2)).replace("<test_size>", str(test_size))
    cur.execute(query)
    con.commit()

    cur.close()
    con.close()

    print("train_size: {}. test_size: {}\n".format(str(train_size), str(test_size)))
    print("========End runSqlScripts()=======")
