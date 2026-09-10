-- Auto-generated schema + seed for Планирование спринтов (PostgreSQL).
-- Regenerate with: python scripts/gen_initsql.py
-- Source of truth for the Java (JPA) and Python (SQLAlchemy) services.

CREATE TABLE IF NOT EXISTS params (
  id           INT PRIMARY KEY DEFAULT 1,
  name         TEXT, start_date TEXT, sprint_days INT, focus DOUBLE PRECISION,
  today_date   TEXT, goal TEXT, sprints INT,
  budget_rate  DOUBLE PRECISION, budget_total DOUBLE PRECISION, ttm_target INT
);
CREATE TABLE IF NOT EXISTS dod        (id SERIAL PRIMARY KEY, crit TEXT, done BOOLEAN, ord INT);
CREATE TABLE IF NOT EXISTS team       (id SERIAL PRIMARY KEY, name TEXT, role TEXT, avail DOUBLE PRECISION, absent DOUBLE PRECISION, ord INT);
CREATE TABLE IF NOT EXISTS tasks      (pk SERIAL PRIMARY KEY, task_id TEXT, title TEXT, assignee TEXT, role TEXT, type TEXT, est DOUBLE PRECISION, status TEXT, sprint INT, dep TEXT, started TEXT, done TEXT, added BOOLEAN, ord INT);
CREATE TABLE IF NOT EXISTS releases   (pk SERIAL PRIMARY KEY, rel_id TEXT, name TEXT, sfrom INT, sto INT, status TEXT, ord INT);
CREATE TABLE IF NOT EXISTS milestones (pk SERIAL PRIMARY KEY, ms_id TEXT, name TEXT, sprint INT, status TEXT, rel TEXT, ord INT);
CREATE TABLE IF NOT EXISTS tech_debt  (pk SERIAL PRIMARY KEY, td_id TEXT, descr TEXT, area TEXT, type TEXT, impact TEXT, est DOUBLE PRECISION, status TEXT, created INT, paid INT, ord INT);
CREATE TABLE IF NOT EXISTS risks      (pk SERIAL PRIMARY KEY, name TEXT, p INT, i INT, mit TEXT, owner TEXT, status TEXT, ord INT);
CREATE TABLE IF NOT EXISTS bugs       (pk SERIAL PRIMARY KEY, bug_id TEXT, descr TEXT, task TEXT, sprint INT, sev TEXT, status TEXT, time_h DOUBLE PRECISION, reopened BOOLEAN, cause TEXT, ord INT);
CREATE TABLE IF NOT EXISTS calendar   (id SERIAL PRIMARY KEY, cdate TEXT, name TEXT, ord INT);
CREATE TABLE IF NOT EXISTS retro      (id SERIAL PRIMARY KEY, sprint INT, well TEXT, improve TEXT, action TEXT, owner TEXT, due TEXT, status TEXT, ord INT);
CREATE TABLE IF NOT EXISTS rice       (pk SERIAL PRIMARY KEY, rice_id TEXT, name TEXT, reach DOUBLE PRECISION, impact DOUBLE PRECISION, conf TEXT, effort DOUBLE PRECISION, ord INT);
CREATE TABLE IF NOT EXISTS deps       (pk SERIAL PRIMARY KEY, dep_id TEXT, item TEXT, type TEXT, task TEXT, stream TEXT, dir TEXT, descr TEXT, sprint INT, status TEXT, owner TEXT, risk TEXT, ord INT);
CREATE TABLE IF NOT EXISTS okr        (id SERIAL PRIMARY KEY, q TEXT, obj TEXT, kr TEXT, target DOUBLE PRECISION, cur DOUBLE PRECISION, ord INT);
CREATE TABLE IF NOT EXISTS app_meta   (id INT PRIMARY KEY DEFAULT 1, version BIGINT DEFAULT 1);


-- params (single row)
INSERT INTO params (id,name,start_date,sprint_days,focus,today_date,goal,sprints,budget_rate,budget_total,ttm_target) VALUES (1,'Sprint 24','2026-08-03',10,0.8,'2026-09-10','Запустить оформление заказа с онлайн-оплатой',11,8000,8000000,15);

-- dod
INSERT INTO dod (crit, done, ord) VALUES ('Код прошёл ревью', FALSE, 0);
INSERT INTO dod (crit, done, ord) VALUES ('Юнит/интеграционные тесты зелёные', FALSE, 1);
INSERT INTO dod (crit, done, ord) VALUES ('Документация обновлена', FALSE, 2);
INSERT INTO dod (crit, done, ord) VALUES ('Развёрнуто на stage', FALSE, 3);
INSERT INTO dod (crit, done, ord) VALUES ('Принято владельцем продукта', FALSE, 4);
INSERT INTO dod (crit, done, ord) VALUES ('Нет открытых блокеров', FALSE, 5);

-- team
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Иванов А.', 'Backend', 1, 0, 0);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Петрова М.', 'Frontend', 1, 0, 1);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Сидоров К.', 'QA', 0.8, 0, 2);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Кузнецов Д.', 'Backend', 1, 0, 3);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Орлова Е.', 'Analyst', 0.5, 0, 4);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Смирнов П.', 'Backend', 1, 0, 5);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Волкова Н.', 'Frontend', 1, 0, 6);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Морозов И.', 'QA', 1, 0, 7);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Новиков А.', 'DevOps', 0.8, 0, 8);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Фёдорова О.', 'Analyst', 1, 0, 9);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Козлов В.', 'Backend', 1, 0, 10);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Лебедева Т.', 'Designer', 0.8, 0, 11);
INSERT INTO team (name, role, avail, absent, ord) VALUES ('Соколов Р.', 'Frontend', 1, 0, 12);

-- tasks
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-01', 'Проектирование API заказов', 'Иванов А.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C5,Капасити!$B$5:$B$147,0)),"")', 'История', 5, 'Готово', 1, '', '2026-08-03', '2026-08-06', FALSE, 0);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-02', 'Экран корзины (вёрстка)', 'Петрова М.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C6,Капасити!$B$5:$B$147,0)),"")', 'Задача', 8, 'Готово', 1, 'T-01', '2026-08-04', '2026-08-12', FALSE, 1);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-09', 'Настройка CI/CD', 'Новиков А.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C7,Капасити!$B$5:$B$147,0)),"")', 'Задача', 4, 'Готово', 1, '', '2026-08-03', '2026-08-05', FALSE, 2);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-10', 'Модель данных заказа', 'Кузнецов Д.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C8,Капасити!$B$5:$B$147,0)),"")', 'История', 5, 'В работе', 1, '', '2026-08-05', NULL, FALSE, 3);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-03', 'Интеграция платежей', 'Иванов А.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C9,Капасити!$B$5:$B$147,0)),"")', 'Задача', 8, 'Готово', 2, 'T-01', '2026-08-17', '2026-08-24', FALSE, 4);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-04', 'Тест-кейсы оформления', 'Сидоров К.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C10,Капасити!$B$5:$B$147,0)),"")', 'Тех.долг', 4, 'Готово', 2, '', '2026-08-18', '2026-08-20', FALSE, 5);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-08', 'Уведомления по e-mail', 'Смирнов П.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C11,Капасити!$B$5:$B$147,0)),"")', 'Задача', 4, 'Готово', 2, '', '2026-08-19', '2026-08-26', FALSE, 6);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-11', 'API промокодов', 'Козлов В.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C12,Капасити!$B$5:$B$147,0)),"")', 'История', 5, 'Готово', 2, '', '2026-08-17', '2026-08-25', FALSE, 7);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-12', 'Логирование и метрики', 'Новиков А.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C13,Капасити!$B$5:$B$147,0)),"")', 'Задача', 3, 'To Do', 2, '', NULL, NULL, FALSE, 8);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-05', 'Рефакторинг авторизации', 'Кузнецов Д.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C14,Капасити!$B$5:$B$147,0)),"")', 'Задача', 3, 'В работе', 3, '', '2026-09-02', NULL, FALSE, 9);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-06', 'Аналитика воронки', 'Орлова Е.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C15,Капасити!$B$5:$B$147,0)),"")', 'История', 3, 'To Do', 3, '', NULL, NULL, TRUE, 10);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-07', 'Регресс-тестирование релиза', 'Сидоров К.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C16,Капасити!$B$5:$B$147,0)),"")', 'Задача', 5, 'To Do', 3, 'T-04', NULL, NULL, FALSE, 11);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-13', 'Экран оплаты', 'Волкова Н.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C17,Капасити!$B$5:$B$147,0)),"")', 'Задача', 8, 'В работе', 3, 'T-03', '2026-09-01', NULL, FALSE, 12);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-14', 'Вебхуки платежей', 'Иванов А.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C18,Капасити!$B$5:$B$147,0)),"")', 'История', 5, 'To Do', 3, 'T-13', NULL, NULL, TRUE, 13);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-15', 'История заказов', 'Соколов Р.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C19,Капасити!$B$5:$B$147,0)),"")', 'Задача', 5, 'To Do', 3, '', NULL, NULL, FALSE, 14);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-16', 'Личный кабинет', 'Волкова Н.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C20,Капасити!$B$5:$B$147,0)),"")', 'Задача', 8, 'To Do', 4, 'T-15', NULL, NULL, FALSE, 15);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-17', 'Фильтры каталога', 'Морозов И.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C21,Капасити!$B$5:$B$147,0)),"")', 'История', 6, 'To Do', 4, 'T-16', NULL, NULL, FALSE, 16);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-18', 'Отзывы и рейтинги', 'Лебедева Т.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C22,Капасити!$B$5:$B$147,0)),"")', 'Тех.долг', 5, 'To Do', 4, '', NULL, NULL, FALSE, 17);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-19', 'Рекомендации', 'Фёдорова О.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C23,Капасити!$B$5:$B$147,0)),"")', 'История', 8, 'To Do', 5, '', NULL, NULL, FALSE, 18);
INSERT INTO tasks (task_id, title, assignee, role, type, est, status, sprint, dep, started, done, added, ord) VALUES ('T-20', 'A/B тесты чекаута', 'Морозов И.', '=IFERROR(INDEX(Капасити!$C$5:$C$147,MATCH($C24,Капасити!$B$5:$B$147,0)),"")', 'Задача', 5, 'To Do', 5, '', NULL, NULL, FALSE, 19);

-- releases
INSERT INTO releases (rel_id, name, sfrom, sto, status, ord) VALUES ('R-1', 'Внутренний релиз (MVP)', 1, 2, 'Готово', 0);
INSERT INTO releases (rel_id, name, sfrom, sto, status, ord) VALUES ('R-2', 'Бета для площадок', 3, 4, 'В работе', 1);
INSERT INTO releases (rel_id, name, sfrom, sto, status, ord) VALUES ('R-3', 'Публичный релиз 1.0', 5, 6, 'Планируется', 2);
INSERT INTO releases (rel_id, name, sfrom, sto, status, ord) VALUES ('R-4', 'Релиз 1.1 — уведомления', 7, 8, 'Планируется', 3);
INSERT INTO releases (rel_id, name, sfrom, sto, status, ord) VALUES ('R-5', 'GA / Стабилизация', 9, 10, 'Планируется', 4);

-- milestones
INSERT INTO milestones (ms_id, name, sprint, status, rel, ord) VALUES ('V-1', 'Старт проекта', 1, 'Готово', 'R-1', 0);
INSERT INTO milestones (ms_id, name, sprint, status, rel, ord) VALUES ('V-2', 'Дизайн утверждён', 2, 'Готово', 'R-1', 1);
INSERT INTO milestones (ms_id, name, sprint, status, rel, ord) VALUES ('V-3', 'Feature freeze', 5, 'Планируется', 'R-3', 2);
INSERT INTO milestones (ms_id, name, sprint, status, rel, ord) VALUES ('V-4', 'Code freeze', 6, 'Планируется', 'R-3', 3);
INSERT INTO milestones (ms_id, name, sprint, status, rel, ord) VALUES ('V-5', 'Go-live / запуск', 7, 'Планируется', 'R-4', 4);

-- tech_debt
INSERT INTO tech_debt (td_id, descr, area, type, impact, est, status, created, paid, ord) VALUES ('TD-1', 'Рефакторинг модуля авторизации', 'Auth', 'Код', 'High', 3, 'Закрыт', 1, 3, 0);
INSERT INTO tech_debt (td_id, descr, area, type, impact, est, status, created, paid, ord) VALUES ('TD-2', 'Автотесты оформления заказа', 'Checkout', 'Тесты', 'High', 2, 'Закрыт', 2, 4, 1);
INSERT INTO tech_debt (td_id, descr, area, type, impact, est, status, created, paid, ord) VALUES ('TD-3', 'Убрать дубли в API заказов', 'API', 'Архитектура', 'Medium', 2, 'Открыт', 3, NULL, 2);
INSERT INTO tech_debt (td_id, descr, area, type, impact, est, status, created, paid, ord) VALUES ('TD-4', 'Обновить документацию API', 'Docs', 'Документация', 'Low', 1, 'Открыт', 4, NULL, 3);
INSERT INTO tech_debt (td_id, descr, area, type, impact, est, status, created, paid, ord) VALUES ('TD-5', 'Мониторинг и алерты платежей', 'Payments', 'Инфраструктура', 'Medium', 2, 'В работе', 3, NULL, 4);
INSERT INTO tech_debt (td_id, descr, area, type, impact, est, status, created, paid, ord) VALUES ('TD-6', 'Оптимизация запросов БД', 'DB', 'Код', 'Medium', 3, 'Открыт', 5, NULL, 5);

-- risks
INSERT INTO risks (name, p, i, mit, owner, status, ord) VALUES ('Зависимость от внешнего API оплаты', 4, 5, 'Мок-сервис + ранняя интеграция', 'Иванов А.', 'Открыт', 0);
INSERT INTO risks (name, p, i, mit, owner, status, ord) VALUES ('Отпуска в декабре (Спринт 11)', 5, 3, 'Сокращённый объём, буфер', 'Орлова Е.', 'Открыт', 1);
INSERT INTO risks (name, p, i, mit, owner, status, ord) VALUES ('Недооценка интеграции', 3, 4, 'Спайк на оценку', 'Кузнецов Д.', 'Открыт', 2);
INSERT INTO risks (name, p, i, mit, owner, status, ord) VALUES ('Текучесть в QA', 2, 4, 'Кросс-ревью, документация', 'Сидоров К.', 'Наблюдение', 3);

-- bugs
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-01', 'Ошибка валидации email', 'T-01', 1, 'Major', 'Закрыт', 0.5, FALSE, 'Интеграция', 0);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-02', 'Падение при пустой корзине', 'T-02', 1, 'Critical', 'Закрыт', 0.5, FALSE, 'Код', 1);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-03', 'Неверный расчёт скидки', 'T-01', 1, 'Major', 'Закрыт', 0.5, FALSE, 'Требования', 2);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-04', 'Съезжает вёрстка на мобильном', 'T-02', 1, 'Minor', 'Закрыт', 0.3, FALSE, 'Тестирование', 3);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-05', 'Таймаут платежа', 'T-03', 1, 'Major', 'Открыт', 0.2, FALSE, 'Интеграция', 4);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-06', 'Дубли заказов', 'T-03', 2, 'Critical', 'Закрыт', 0.4, TRUE, 'Код', 5);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-07', 'Не приходит письмо-подтверждение', 'T-08', 2, 'Major', 'Закрыт', 0.3, FALSE, 'Требования', 6);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-08', 'Ошибка 500 при оплате', 'T-03', 2, 'Critical', 'Закрыт', 0.3, FALSE, 'Интеграция', 7);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-09', 'Неверный НДС в чеке', 'T-06', 2, 'Major', 'Закрыт', 0.2, FALSE, 'Данные', 8);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-10', 'Кнопка оформления неактивна', 'T-02', 2, 'Minor', 'Закрыт', 0.1, FALSE, 'Код', 9);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-11', 'Переполнение логов', 'T-05', 2, 'Minor', 'Закрыт', 0.2, FALSE, 'Требования', 10);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-12', 'Медленный поиск заказов', 'T-04', 3, 'Major', 'Открыт', 0, FALSE, 'Тестирование', 11);
INSERT INTO bugs (bug_id, descr, task, sprint, sev, status, time_h, reopened, cause, ord) VALUES ('B-13', 'Падает экспорт отчёта', 'T-07', 3, 'Minor', 'Открыт', 0, FALSE, 'Интеграция', 12);

-- calendar
INSERT INTO calendar (cdate, name, ord) VALUES ('2026-11-04', 'День народного единства', 0);
INSERT INTO calendar (cdate, name, ord) VALUES ('2027-01-01', 'Новый год', 1);
INSERT INTO calendar (cdate, name, ord) VALUES ('2027-01-02', 'Новогодние каникулы', 2);

-- retro
INSERT INTO retro (sprint, well, improve, action, owner, due, status, ord) VALUES (1, 'Быстрый старт, реалистичная оценка', 'Мало тестовых данных', 'Подготовить набор тест-данных', 'Сидоров К.', 'Спринт 2', 'Сделано', 0);
INSERT INTO retro (sprint, well, improve, action, owner, due, status, ord) VALUES (1, 'Хорошее демо', 'Долгий код-ревью', 'SLA на ревью — 1 день', 'Иванов А.', 'Спринт 2', 'Сделано', 1);
INSERT INTO retro (sprint, well, improve, action, owner, due, status, ord) VALUES (2, 'Стабильные демо', 'Скоуп рос по ходу', 'Фиксировать скоуп на планировании', 'Кузнецов Д.', 'Спринт 3', 'В работе', 2);
INSERT INTO retro (sprint, well, improve, action, owner, due, status, ord) VALUES (2, 'Слаженная работа QA', 'Блокеры по внешнему API', 'Ранняя интеграция / моки', 'Иванов А.', 'Спринт 3', 'Открыт', 3);

-- rice
INSERT INTO rice (rice_id, name, reach, impact, conf, effort, ord) VALUES ('F-01', 'MVP оформления заказа', 5000, 3, '100%', 40, 0);
INSERT INTO rice (rice_id, name, reach, impact, conf, effort, ord) VALUES ('F-02', 'Оплата картой', 5000, 3, '80%', 25, 1);
INSERT INTO rice (rice_id, name, reach, impact, conf, effort, ord) VALUES ('F-03', 'Промокоды и скидки', 3000, 1, '80%', 12, 2);
INSERT INTO rice (rice_id, name, reach, impact, conf, effort, ord) VALUES ('F-04', 'Уведомления (e-mail/push)', 4000, 1, '80%', 15, 3);
INSERT INTO rice (rice_id, name, reach, impact, conf, effort, ord) VALUES ('F-05', 'История заказов', 3500, 0.5, '100%', 10, 4);
INSERT INTO rice (rice_id, name, reach, impact, conf, effort, ord) VALUES ('F-06', 'Мобильная вёрстка', 4500, 2, '80%', 20, 5);
INSERT INTO rice (rice_id, name, reach, impact, conf, effort, ord) VALUES ('F-07', 'Личный кабинет', 3000, 1, '50%', 18, 6);
INSERT INTO rice (rice_id, name, reach, impact, conf, effort, ord) VALUES ('F-08', 'Рекомендации товаров', 2000, 2, '50%', 22, 7);
INSERT INTO rice (rice_id, name, reach, impact, conf, effort, ord) VALUES ('F-09', 'Экспорт отчётов', 800, 0.5, '80%', 8, 8);
INSERT INTO rice (rice_id, name, reach, impact, conf, effort, ord) VALUES ('F-10', 'Мультиязычность', 1500, 1, '50%', 30, 9);

-- deps
INSERT INTO deps (dep_id, item, type, task, stream, dir, descr, sprint, status, owner, risk, ord) VALUES ('D-01', 'Интеграция платежей', 'Задача', 'T-03', 'Платёжный шлюз', 'Мы зависим', 'API оплаты v2 (токенизация карт)', 3, 'Заблокировано', 'Команда Payments', 'High', 0);
INSERT INTO deps (dep_id, item, type, task, stream, dir, descr, sprint, status, owner, risk, ord) VALUES ('D-02', 'Оплата картой', 'Фича', '', 'Платёжный шлюз', 'Мы зависим', 'Сертификация PCI DSS', 4, 'Ожидается', 'Security / Payments', 'High', 1);
INSERT INTO deps (dep_id, item, type, task, stream, dir, descr, sprint, status, owner, risk, ord) VALUES ('D-03', 'Уведомления (e-mail/push)', 'Задача', 'T-08', 'Инфраструктура / DevOps', 'Мы зависим', 'Сервис рассылок (SMTP + Push)', 4, 'Подтверждено', 'Platform Team', 'Medium', 2);
INSERT INTO deps (dep_id, item, type, task, stream, dir, descr, sprint, status, owner, risk, ord) VALUES ('D-04', 'API промокодов', 'Задача', 'T-11', 'Каталог / Контент', 'Мы зависим', 'Каталог товаров и цен', 2, 'Получено', 'Catalog Team', 'Low', 3);
INSERT INTO deps (dep_id, item, type, task, stream, dir, descr, sprint, status, owner, risk, ord) VALUES ('D-05', 'Личный кабинет', 'История', '', 'Идентификация (SSO)', 'Мы зависим', 'Единый вход (OAuth2/OIDC)', 5, 'Ожидается', 'IAM Team', 'Medium', 4);
INSERT INTO deps (dep_id, item, type, task, stream, dir, descr, sprint, status, owner, risk, ord) VALUES ('D-06', 'Экран корзины', 'Фича', 'T-02', 'Мобильное приложение', 'Зависят от нас', 'REST API заказов для мобильного клиента', 6, 'Подтверждено', 'Mobile Team', 'Medium', 5);
INSERT INTO deps (dep_id, item, type, task, stream, dir, descr, sprint, status, owner, risk, ord) VALUES ('D-07', 'Логирование и метрики', 'Задача', 'T-12', 'Data Platform / Аналитика', 'Мы зависим', 'Шина событий (Kafka topics)', 4, 'Заблокировано', 'Data Platform', 'High', 6);
INSERT INTO deps (dep_id, item, type, task, stream, dir, descr, sprint, status, owner, risk, ord) VALUES ('D-08', 'Экспорт отчётов', 'Фича', '', 'Data Platform / Аналитика', 'Зависят от нас', 'Витрина заказов для BI', 7, 'Ожидается', 'Analytics', 'Low', 7);

-- okr
INSERT INTO okr (q, obj, kr, target, cur, ord) VALUES ('Q3 2026', 'Запустить подписочную модель', 'Готовность MVP чекаута, %', 100, 70, 0);
INSERT INTO okr (q, obj, kr, target, cur, ord) VALUES ('Q3 2026', 'Запустить подписочную модель', 'Интеграция оплаты, %', 100, 60, 1);
INSERT INTO okr (q, obj, kr, target, cur, ord) VALUES ('Q3 2026', 'Обеспечить качество релиза', 'Покрытие автотестами, %', 80, 45, 2);
INSERT INTO okr (q, obj, kr, target, cur, ord) VALUES ('Q4 2026', 'Масштабировать на площадки', 'Подключено площадок, шт', 20, 6, 3);

-- meta
INSERT INTO app_meta (id, version) VALUES (1, 1);
