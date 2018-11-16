create table user_project_description
as 
	select distinct user_id, description 
	from (
		select distinct user_id, repo_id
		from issue_comments c, issues i
		where c.issue_id = i.id
		union
		select distinct user_id, repo_id
		from watchers
		union
		select distinct user_id, repo_id
		from project_members
		union
		select distinct author_id, project_id
		from commits
	) a, projects p
	where a.repo_id = p.id
