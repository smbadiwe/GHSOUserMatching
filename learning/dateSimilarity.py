import psycopg2 as psql
from appUtils import getDbConnection, computeDateSim


def generateDateSimilarity(cfg, redoSimilarity = False):
    print("\n===========\nRUNNING generateDateSimilarity()\n===========\n")
    con, cur = getDbConnection(cfg)
    
    # check if done before
    if redoSimilarity:
        cur.execute('delete from similarities_among_dates')
        con.commit()
    else:
        cur.execute('select g_id from similarities_among_dates limit 1')
        existing = [r[0] for r in cur.fetchall()]
        if len(existing) > 0:
            print("similarities_among_dates has already been generated")
            return

    print("created table similarities_among_dates")

    ### Load user pairs with date
    cur.execute('''
		select distinct g.id, s.id, g.created_at::date, s.creation_date
		from users g, labeled_data l, so_users s
		where g.created_at is not null and g.id = l.g_id
			and s.creation_date is not null and s.id = l.s_id
	''')

    pairs = cur.fetchall()
    for p in pairs:
        sim = computeDateSim(p[2], p[3])
        cur.execute('''
			insert into similarities_among_dates
			values (%s, %s, %s)
		''', (p[0], p[1], sim))

    con.commit()
    cur.close()
    con.close()
    print("=============End=============")
