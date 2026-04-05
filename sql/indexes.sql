USE CallHub;

-- Index on Member name (used in search)
CREATE INDEX idx_member_name ON Member(member_name);

-- Index on Member email (used in login and search)
CREATE INDEX idx_member_email ON Member(iit_email);

-- Index on Member department (used in joins and filters)
CREATE INDEX idx_member_dept ON Member(department_id);

-- Index on Member_Role member_id (used in joins)
CREATE INDEX idx_member_role_mid ON Member_Role(member_id);

-- Index on Search_Log search_time (used in analytics)
CREATE INDEX idx_search_time ON Search_Log(search_time);

-- Index on Search_Log member_id
CREATE INDEX idx_search_member ON Search_Log(member_id);

-- Index on Directory_Interaction_Log actor
CREATE INDEX idx_interaction_actor ON Directory_Interaction_Log(actor_member_id);

-- Index on Directory_Interaction_Log target
CREATE INDEX idx_interaction_target ON Directory_Interaction_Log(target_member_id);

-- Index on Login_History member_id
CREATE INDEX idx_login_member ON Login_History(member_id);

-- Index on Audit_Log performed_by
CREATE INDEX idx_audit_performed ON Audit_Log(performed_by_member_id);