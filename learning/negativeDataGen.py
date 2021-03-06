# -*- coding: utf-8 -*-
from appUtils import getDbConnection


def generateNegativeDataPairs(cfg, redo=False):
    print("\n===========\nRUNNING generateNegativeDataPairs()\n===========\n")
    ### Connect to database
    con, cur = getDbConnection(cfg)

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

    # check if common_users table has been populated
    print("check if gh_so_common_users table has been populated")
    cur.execute('select gh_user_id from gh_so_common_users limit 1')
    existing = [r[0] for r in cur.fetchall()]
    if len(existing) == 0:
        import csv
        import os
        print("populate gh_so_common_users table")
        root_dir = os.path.join(os.path.dirname(__file__), "../")

        with open(root_dir + "data/common_users.csv", "r") as f:
            reader = csv.reader(f)
            values = ["({},{})".format(row[0], row[1]) for row in reader]

        cur.execute('insert into gh_so_common_users (gh_user_id, so_user_id) values {}'
                    .format(values))
        con.commit()
        print("gh_so_common_users table populated")

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

    print("Done generating negative_user_pairs.")
    cur.close()
    con.close()
    print("========End generateNegativeDataPairs()=======")
