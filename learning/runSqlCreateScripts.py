import psycopg2 as psql
from appUtils import get_db_config


def runSqlScripts():
    print("\n===========\nRUNNING runSqlScripts()\n===========\n")
    cfg = get_db_config()
    con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
    cur = con.cursor()

    with open("../sqlscripts/createView.sql", 'r') as r:
        query = r.read()
    cur.execute(query)

    with open("../sqlscripts/user_project_dec_mapping.sql", 'r') as r:
        query = r.read()
    cur.execute(query)

    con.commit()

    cur.close()
    con.close()
    print("========End=======")