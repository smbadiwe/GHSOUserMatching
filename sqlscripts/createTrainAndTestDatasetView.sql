drop view if exists labeled_data_test;
drop view if exists labeled_data;
drop view if exists labeled_data_all;

-- this gives all the data we have for both training and test

create view labeled_data_all as
	select g_id, s_id, g_name, s_name, label
	from (select c.gh_user_id as g_id, c.so_user_id as s_id, g.name as g_name, s.display_name as s_name, 1 as label
	from users g, so_users s, gh_so_common_users c
	where g.id = c.gh_user_id and s.id = c.so_user_id
	and g.name is not null and g.name != ''
	and s.display_name is not null and s.display_name != ''
  ) pos
		union
	select g_id, s_id, g_name, s_name, label
	from (select c.gh_user_id as g_id, c.so_user_id as s_id, g.name as g_name, s.display_name as s_name, 0 as label
	from users g, so_users s, negative_user_pairs c
	where g.id = c.gh_user_id and s.id = c.so_user_id
	and g.name is not null and g.name != ''
	and s.display_name is not null and s.display_name != ''
  ) neg;

-- these give the training data and you can adjust the number of samples

create view labeled_data as
	select g_id, s_id, g_name, s_name, label
	from (select c.gh_user_id as g_id, c.so_user_id as s_id, g.name as g_name, s.display_name as s_name, 1 as label
	from users g, so_users s, gh_so_common_users c
	where g.id = c.gh_user_id and s.id = c.so_user_id
	and g.name is not null and g.name != ''
	and s.display_name is not null and s.display_name != ''
	limit <train_size>) pos
		union
	select g_id, s_id, g_name, s_name, label
	from (select c.gh_user_id as g_id, c.so_user_id as s_id, g.name as g_name, s.display_name as s_name, 0 as label
	from users g, so_users s, negative_user_pairs c
	where g.id = c.gh_user_id and s.id = c.so_user_id
	and g.name is not null and g.name != ''
	and s.display_name is not null and s.display_name != ''
	limit <train_size>) neg;

create view labeled_data_test as
  select f.g_id, f.s_id, f.g_name, f.s_name, f.label from (
    select g_id, s_id, g_name, s_name, label
    from labeled_data_all
    except
    select g_id, s_id, g_name, s_name, label
    from labeled_data
  ) f
  limit <test_size>;
