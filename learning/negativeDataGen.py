# -*- coding: utf-8 -*-

import psycopg2 as psql
from appUtils import get_db_config


def generateNegativeDataPairs(redo = False):
    print("\n===========\nRUNNING generateNegativeDataPairs()\n===========\n")
    ### Connect to database
    cfg = get_db_config()
    con = psql.connect(host=cfg["host"], user=cfg["user"], database=cfg["database"], password=cfg["password"])
    cur = con.cursor()

    cur.execute('''
    		create table if not exists negative_user_pairs
    			(gh_user_id int, so_user_id int)
    	''')

    if redo:
        cur.execute('delete from negative_user_pairs')
        con.commit()
    else:
        # Check if done before
        cur.execute('select gh_user_id from negative_user_pairs limit 1')
        existing = [r[0] for r in cur.fetchall()]
        if len(existing) > 0:
            print("negative_user_pairs has already been generated")
            return

    print("Generating negative_user_pairs...")

    ### Load GH users (positive)
    cur.execute('select distinct gh_user_id from gh_so_common_users')
    gh_users = [r[0] for r in cur.fetchall()]

    ### Load SO users (positive)
    cur.execute('select distinct so_user_id from gh_so_common_users')
    so_users = [r[0] for r in cur.fetchall()]

    ### Load SO users (negative)
    cur.execute('''
		select *
		from (
			select id
			from so_users 
			except 
			select so_user_id
			from gh_so_common_users
		) as a
		order by random()
		limit %s
	''', (len(gh_users),))

    ### Pairing with GH positive users and SO negative users,
    ### generate nagative samples w.r.t. GH positive users
    out = ['(%d, %d)' % p for p in zip(gh_users, [r[0] for r in cur.fetchall()])]
    cur.execute('''
		insert into negative_user_pairs (gh_user_id, so_user_id) 
		values %s 
	''' % ','.join(out))

    ### Load GH users (negative)
    cur.execute('''
		select *
		from (
			select id
			from users 
			except 
			select gh_user_id
			from gh_so_common_users
		) as a
		order by random()
		limit %s
	''', (len(so_users),))

    ### Pairing with GH positive users and SO negative users,
    ### generate nagative samples w.r.t. GH positive users
    out = ['(%d, %d)' % p for p in zip(so_users, [r[0] for r in cur.fetchall()])]
    cur.execute('''
		insert into negative_user_pairs 
		values %s 
	''' % ','.join(out))
    con.commit()

    print("Done generating negative_user_pairs. \nNow create the combined view 'labeled_data'...")
    with open("./createView.sql", 'r') as r:
        query = r.read()
    cur.execute(query)
    con.commit()

    cur.close()
    con.close()
    print("========End=======")
