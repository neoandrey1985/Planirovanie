-- v1.53: метки этапов на «Ганте по иерархии» — ручные даты этапов задачи (JSON: ba_s, ba_e, … prod_e)
-- и соответствие этапов ролям для автоматического режима (ba=Product Owner;sa=Analyst;…).

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS stages TEXT;
ALTER TABLE params ADD COLUMN IF NOT EXISTS stage_roles TEXT;
