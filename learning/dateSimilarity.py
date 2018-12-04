import psycopg2 as psql
from appUtils import get_db_config


def generateDateSimilarity(redoSimilarity = False):
    print("\n===========\nRUNNING generateDateSimilarity()\n===========\n")
    cfg = get_db_config()
    con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
    cur = con.cursor()

    ### create table for date similarity
    cur.execute('''
		create table if not exists similarities_among_dates
			(g_id int, s_id int, similarity float8, primary key(g_id, s_id))
	''')

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
        g_date, s_date = p[2], p[3]
        if g_date > s_date:
            num = g_date - s_date
        else:
            num = s_date - g_date

        ### Calculate similarity
        if num.days == 0:
            sim = 1
        else:
            sim = 1.0 / num.days
        cur.execute('''
			insert into similarities_among_dates
			values (%s, %s, %s)
		''', (p[0], p[1], sim))

    con.commit()
    cur.close()
    con.close()
