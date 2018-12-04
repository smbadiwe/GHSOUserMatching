# -*- coding: utf-8 -*-

import psycopg2 as psql
from learning.appUtils import get_db_config

def main():
	print("\n===========\nRUNNING generateDescAboutMeSimilarity()\n===========\n")
	cfg = get_db_config()
	con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
	cur = con.cursor()

	cur.execute('''
		select g_id, s_id, probability
		from predicted
	''')

	w = open('../data/predicted.tsv', 'w')

	for row in cur.fetchall():
		w.write("\t".join([str(r) for r in row]) + "\n")

	w.close()

	cur.close()
	con.close()


if __name__ == "__main__":
    main()
