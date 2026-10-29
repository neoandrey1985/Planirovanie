-- v1.50: «Мой профиль» — привязка учётной записи к участнику команды (имя из раздела «Команда»).

ALTER TABLE app_users ADD COLUMN IF NOT EXISTS member_name TEXT;
