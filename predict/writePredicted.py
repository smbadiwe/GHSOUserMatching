# -*- coding: utf-8 -*-

import psycopg2 as psql


def main():
	con = psql.connect('dbname=gh_so')
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
