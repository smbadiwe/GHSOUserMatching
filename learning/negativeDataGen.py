# -*- coding: utf-8 -*-

import psycopg2 as psql

def main():
	### Connect to database
	con = psql.connect(host="localhost", user='postgres', database="gh_so", password="P@ssw0rd") # 123andro321
	cur = con.cursor()
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
	''', (len(gh_users),) )

	### Pairing with GH positive users and SO negative users,
	### generate nagative samples w.r.t. GH positive users
	out = ['(%d, %d)' % p for p in zip(gh_users, [r[0] for r in cur.fetchall()])]
	cur.execute('''
		insert into negative_user_pairs (gh_user_id, so_user_id) 
		values %s 
	''' % ','.join(out) )

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
	''', (len(so_users),) )

	### Pairing with GH positive users and SO negative users,
	### generate nagative samples w.r.t. GH positive users
	out = ['(%d, %d)' % p for p in zip(so_users, [r[0] for r in cur.fetchall()])]
	cur.execute('''
		insert into negative_user_pairs 
		values %s 
	''' % ','.join(out) )

	con.commit()
	cur.close()
	con.close()

if __name__ == "__main__":
    main()
