drop view labeled_data;
create view labeled_data as
	select g_id, s_id, g_name, s_name, label
	from (select c.gh_user_id as g_id, c.so_user_id as s_id, g.name as g_name, s.display_name as s_name, 1 as label
	from users g, so_users s, gh_so_common_users c
	where g.id = c.gh_user_id and s.id = c.so_user_id
	and g.name is not null and g.name != ''
	and s.display_name is not null and s.display_name != ''
	limit 10) pos
		union
	select g_id, s_id, g_name, s_name, label
	from (select c.gh_user_id as g_id, c.so_user_id as s_id, g.name as g_name, s.display_name as s_name, 0 as label
	from users g, so_users s, negative_user_pairs c
	where g.id = c.gh_user_id and s.id = c.so_user_id
	and g.name is not null and g.name != ''
	and s.display_name is not null and s.display_name != ''
	limit 10) neg;