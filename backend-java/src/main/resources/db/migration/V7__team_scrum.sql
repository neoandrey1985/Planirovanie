-- Flyway V7: additional "Scrum Master" role on team members.
-- The primary role stays in team.role (Backend/Frontend/QA/DevOps/Analyst/Designer/Product Owner/ИТ-Лидер);
-- team.scrum = 'Да' marks a member who is also a Scrum Master (an additional role).

ALTER TABLE team ADD COLUMN IF NOT EXISTS scrum TEXT;
