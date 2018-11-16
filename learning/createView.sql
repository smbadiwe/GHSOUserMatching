create view labeled_data as
	select c.gh_user_id as g_id, c.so_user_id as s_id, 1 as label 
	from gh_so_common_users c
	union
	select c.gh_user_id as g_id, c.so_user_id as s_id, 0 as label 
	from users g, so_users s, negative_user_pairs c
