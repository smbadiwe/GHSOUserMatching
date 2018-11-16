# -*- coding: utf-8 -*-

import psycopg2 as psql

def main():
	con = psql.connect('dbname=gh_so')
	cur = con.cursor()

	### create table for date similarity
	cur.execute('''
		create table similarities_among_dates
			(g_id int, s_id int, similarity float8, primary key(g_id, s_id))
	''')

	### Load user pairs with date
	cur.execute('''
		select distinct g.id, s.id, g.created_at::date, s.creation_date
		from users g, labeled_data l, so_users s
		where g.created_at is not null and g.id = l.g_id
			and s.creation_date is not null and s.id = l.s_id
	''')

	pairs = cur.fetchall()
	for p in pairs:
		g_date, s_date = p[2], p[3]
		if g_date > s_date:
			num = g_date - s_date
		else:
			num = s_date - g_date

		### Calculate similarity
		if num.days == 0:
			sim = 1
		else:
			sim = 1.0/num.days
		cur.execute('''
			insert into similarities_among_dates
			values (%s, %s, %s)
		''', (p[0], p[1], sim))

	con.commit()
	cur.close()
	con.close()



if __name__ == "__main__":
    main()
