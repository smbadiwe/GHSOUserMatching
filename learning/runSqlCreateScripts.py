from appUtils import getDbConnection
import os


def runSqlScripts(cfg, train_size, test_size):
    print("\n===========\nRUNNING runSqlScripts()\n===========\n")
    con, cur = getDbConnection(cfg)
    root_dir = os.path.join(os.path.dirname(__file__), "../")
    
    print("Running createTables.sql script")
    with open(root_dir + "sqlscripts/createTables.sql", 'r') as r:
        query = r.read()
    cur.execute(query)
    con.commit()

    print("Running user_project_dec_mapping.sql script")
    with open(root_dir + "sqlscripts/user_project_dec_mapping.sql", 'r') as r:
        query = r.read()
    cur.execute(query)
    con.commit()

    print("Running createTrainAndTestDatasetView.sql script")
    with open(root_dir + "sqlscripts/createTrainAndTestDatasetView.sql", 'r') as r:
        query = r.read()
    query = query.replace("<train_size>", str(train_size // 2)).replace("<test_size>", str(test_size))
    cur.execute(query)
    con.commit()

    cur.close()
    con.close()

    print("train_size: {}. test_size: {}\n".format(str(train_size), str(test_size)))
    print("========End runSqlScripts()=======")
