# -*- coding: utf-8 -*-
"""Regenerate «Тестовая документация».docx — тест-план, тест-кейсы и тестовые сценарии.

Документ автогенерируется из реального набора тестов, поэтому не устаревает:
  • фронтенд  — имена `case('…')` из tests/frontend/run_e2e.py + разделы из NAV (frontend/index.html);
  • backend   — методы @Test из backend-java/src/test/**/*.java;
  • analytics — файлы тестов analytics-python/tests/*.py.
Версия берётся из APP_VERSION. Кладётся в папку «Тестовая документация» (в раздел «Support» не входит).

Запуск:  python scripts/deliverables/build_test_docs.py
Зависимости:  python-docx.
"""
import re, glob, pathlib, datetime
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = pathlib.Path(__file__).resolve().parents[2]
INDEX = ROOT / "frontend" / "index.html"
E2E = ROOT / "tests" / "frontend" / "run_e2e.py"
JAVA_TESTS = ROOT / "backend-java" / "src" / "test"
PY_TESTS = ROOT / "analytics-python" / "tests"
OUTDIR = ROOT / "Тестовая документация"
OUT = OUTDIR / "Тестовая_документация_Планирование_спринта_PRO.docx"


def app_version():
    m = re.search(r"APP_VERSION\s*=\s*'([^']+)'", INDEX.read_text(encoding="utf-8"))
    return m.group(1) if m else "—"


def nav_sections():
    """[(id, label, group)] из массива NAV."""
    txt = INDEX.read_text(encoding="utf-8")
    block = re.search(r"const NAV=\[(.*?)\];", txt, re.S).group(1)
    out = []
    for g in re.finditer(r"\{g:'([^']+)',items:\[(.*?)\]\}", block, re.S):
        group = g.group(1)
        for it in re.finditer(r"\['([^']+)','([^']+)'", g.group(2)):
            out.append((it.group(1), it.group(2), group))
    return out


def e2e_cases():
    """Имена case('…') из run_e2e.py в порядке объявления; флаг — это smoke-цикл по разделам."""
    out = []
    for m in re.finditer(r"case\(\s*'([^']+)'", E2E.read_text(encoding="utf-8")):
        name = m.group(1)
        out.append(name)
    return out


# человекочитаемое назначение backend-методов (fallback — само имя метода)
JAVA_PURPOSE = {
    "stateRoundTripAndVersioning": "Снимок состояния: round-trip всех коллекций через PUT/GET /api/state и оптимистичная блокировка версией (app_meta)",
    "enforcesAuthAndRoles": "Авторизация и роли: доступ к защищённым эндпоинтам по ролям (admin/editor/viewer)",
    "throttlesBruteForceLogin": "Безопасность: throttling входа — защита от перебора пароля",
    "logsEventsToSeparateDatabase": "Аудит: бизнес-события пишутся в отдельную БД аудита",
    "relaysOpsAndPresence": "Доска (WebSocket): ретрансляция операций и присутствия участников",
    "notConfiguredByDefault": "Интеграции: по умолчанию выключены — приложение работает офлайн",
    "detectsConfiguration": "Интеграции: включение/детект настроек через переменные окружения",
}
PY_PURPOSE = {
    "test_compute.py": "Движок метрик (compute): velocity, health, зависимости, RICE — форма и диапазоны значений",
    "test_db_integration.py": "Интеграция аналитики с БД: чтение состояния и расчёт метрик на реальной схеме",
}


def java_tests():
    """[(class, method, purpose)]."""
    out = []
    for f in sorted(glob.glob(str(JAVA_TESTS / "**" / "*.java"), recursive=True)):
        txt = pathlib.Path(f).read_text(encoding="utf-8")
        cls = re.search(r"class\s+(\w+)", txt)
        cls = cls.group(1) if cls else pathlib.Path(f).stem
        methods = re.findall(r"@Test[\s\S]{0,80}?void\s+(\w+)\s*\(", txt)
        for mth in methods:
            out.append((cls, mth, JAVA_PURPOSE.get(mth, re.sub(r"(?<!^)(?=[A-Z])", " ", mth).lower())))
    return out


# ---------- сценарии (end-to-end пользовательские потоки), привязаны к функционалу ----------
SCENARIOS = [
    ("SC-01", "Вход и разграничение прав",
     "Открыть приложение → войти как viewer/editor/admin → проверить доступ к действиям (save гейтится правами).",
     "Чтение доступно всем; запись/действия — только editor/admin; админ-функции — только admin."),
    ("SC-02", "Планирование спринта",
     "Задать параметры (старт, число спринтов, focus factor) → заполнить команду → авто-набор спринта по ёмкости.",
     "Дорожная карта пересчитывается: даты, ёмкость, план, velocity, % выполнения."),
    ("SC-03", "Наполнение и приоритизация бэклога",
     "Создать задачи → отсортировать по приоритету (RICE/MoSCoW/WSJF) → назначить спринт/релиз.",
     "Приоритеты и порядок пересчитываются; данные питают план, Гант и аналитику."),
    ("SC-04", "Церемонии Scrum",
     "Провести дэйли, груминг, Planning Poker, демо и ретроспективу.",
     "Записи сохраняются; Poker показывает медиану/консенсус; ретро копит action items."),
    ("SC-05", "Выпуск релиза",
     "Сформировать состав релиза (релизная доска) → проверить вехи и зависимости.",
     "Состав и уверенность релиза считаются; заблокированные зависимости подсвечиваются."),
    ("SC-06", "Аналитика и качество",
     "Открыть аналитику, EVM, DORA, риски, баги, инциденты.",
     "Метрики (velocity, burndown, CFD, CPI/SPI, DORA-тиры, DRE) считаются и визуализируются."),
    ("SC-07", "Здоровье и улучшения",
     "Bus factor, Team Health Check, импедименты, уроки, Agile-зрелость.",
     "Показатели здоровья команды и улучшений рассчитываются и отображаются."),
    ("SC-08", "Помощник (чат-бот)",
     "Спросить про любой раздел, список разделов, «что нового»; выполнить команду («набери спринт N»).",
     "Помощник отвечает по всем разделам (самообучаемая база знаний) и выполняет действия с учётом прав."),
    ("SC-09", "Экспорт и отчётность",
     "Экспорт Excel; отчёт-презентация (PPTX); статус-отчёт.",
     "Excel — валидный пакет; PPTX собирается со всеми слайдами без повреждений; статус-отчёт формируется из данных."),
    ("SC-10", "Интерактивная доска",
     "Добавить стикеры/фигуры, связи, анимацию; экспорт.",
     "Элементы добавляются и сохраняются; связи строятся; холст экспортируется."),
    ("SC-11", "Качество и целостность данных",
     "Запустить «Проверки данных» и EDA; при необходимости авто-исправление.",
     "Линтер данных находит проблемы и чинит; EDA строит KPI, графики и таблицы полноты."),
    ("SC-12", "Сохранение и миграции состояния",
     "Изменить данные → сохранить → перезагрузить; прогнать миграции состояния.",
     "migrate() идемпотентна; save() персистит; снимок восстанавливается с версией."),
]


def pretty_area(name):
    return name.split(":")[0].strip() if ":" in name else "Общее"


def pretty_check(name):
    return name.split(":", 1)[1].strip() if ":" in name else name.strip()


def tbl(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        t.rows[0].cells[i].text = ""; r = t.rows[0].cells[i].paragraphs[0].add_run(h); r.bold = True
    for row in rows:
        c = t.add_row().cells
        for i, v in enumerate(row):
            c[i].text = str(v)
    return t


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    VER = app_version()
    today = datetime.date.today().strftime("%d.%m.%Y")
    secs = nav_sections()
    cases = e2e_cases()
    jtests = java_tests()
    ptests = [(pathlib.Path(f).name, PY_PURPOSE.get(pathlib.Path(f).name, "тест аналитики"))
              for f in sorted(glob.glob(str(PY_TESTS / "*.py")))]

    # frontend e2e → строки тест-кейсов; smoke-цикл по разделам сворачиваем в один кейс
    fe_rows, smoke = [], False
    for name in cases:
        if name.startswith("section renders"):
            smoke = True; continue
        fe_rows.append((pretty_area(name), pretty_check(name)))

    doc = docx.Document()
    doc.styles["Normal"].font.name = "Calibri"; doc.styles["Normal"].font.size = Pt(11)

    doc.add_heading("Тестовая документация", level=0)
    doc.add_paragraph().add_run("Управление кросс-функциональной командой · v%s · %s" % (VER, today)).italic = True
    doc.add_paragraph(
        "Тест-план, тестовые сценарии и тест-кейсы приложения для управления кросс-функциональной командой. "
        "Документ генерируется из реального набора автотестов (frontend e2e, backend MockMvc, analytics) и "
        "обновляется при каждом релизе — перечень кейсов всегда соответствует коду.")

    # 1. Тест-план
    doc.add_heading("1. Тест-план", level=1)
    doc.add_heading("1.1. Объект и цель", level=2)
    doc.add_paragraph(
        "Объект — полиглот-приложение: SPA (frontend/index.html), backend Spring Boot + PostgreSQL "
        "(Flyway-миграции) и сервис аналитики (FastAPI). Цель тестирования — подтвердить, что весь "
        "функционал работает корректно на каждом релизе (регрессия по всему приложению).")
    doc.add_heading("1.2. Уровни тестирования", level=2)
    for line in [
        "Модульный/компонентный — расчётные функции аналитики (Python) и доменные операции backend.",
        "Интеграционный — REST API и авторизация (Spring Boot + H2 через MockMvc), интеграция аналитики с БД.",
        "Сквозной (e2e) — UI в headless Chromium (Playwright): рендер разделов, метрики, экспорт, права.",
        "Регрессионный — единый прогон покрывает весь функционал и запускается перед каждым коммитом и в CI.",
    ]:
        doc.add_paragraph(line, style="List Bullet")
    doc.add_heading("1.3. Среды и инструменты", level=2)
    tbl(doc, ["Слой", "Среда / инструмент", "Как запускается"], [
        ["Frontend e2e", "Python + Playwright (headless Chromium), статический сервер", "make test-frontend → tests/frontend/run_e2e.py"],
        ["Backend", "Spring Boot + H2 (in-memory), MockMvc", "make test-java → mvn -B -ntp test (в песочнице: mvn -o test)"],
        ["Analytics", "Python (скрипт-ассерты)", "make test-python → analytics-python/tests/*.py"],
        ["Полная регрессия", "все три слоя", "make test"],
    ])
    doc.add_heading("1.4. Критерии входа и выхода", level=2)
    for line in [
        "Вход: сборка собирается; окружение поднимается одной командой; демо-данные загружаются.",
        "Выход (приёмка релиза): все тесты зелёные (frontend + Java + Python); APP_VERSION совпадает с головой CHANGELOG; "
        "сопутствующие документы и эта тест-документация обновлены.",
        "Красный тест — блокер релиза; чинится причина, а не тест.",
    ]:
        doc.add_paragraph(line, style="List Bullet")
    doc.add_heading("1.5. Управление дефектами и риски", level=2)
    doc.add_paragraph(
        "Дефекты ведутся в разделах приложения «Баги» и «Проблемы» (журнал проблем), критичные — эскалируются. "
        "Основные риски: смена демо-данных (seed) — тесты проверяют форму и диапазоны, а не точные значения; "
        "недоступность живого Tomcat в песочнице — backend проверяется через MockMvc (mvn -o test).")

    # 2. Тестовые сценарии
    doc.add_heading("2. Тестовые сценарии", level=1)
    doc.add_paragraph("Сквозные пользовательские потоки. Каждый сценарий покрывается автотестами из раздела 3 "
                      "и ручной проверкой при приёмке релиза.")
    tbl(doc, ["ID", "Сценарий", "Шаги / поток", "Ожидаемый результат"],
        [[s[0], s[1], s[2], s[3]] for s in SCENARIOS])

    # 3. Тест-кейсы
    doc.add_heading("3. Тест-кейсы", level=1)
    total = len(fe_rows) + (1 if smoke else 0) + len(jtests) + len(ptests)
    doc.add_paragraph("Всего автоматизированных проверок: %d (frontend e2e: %d%s; backend: %d; analytics: %d). "
                      "Все кейсы автоматизированы и входят в регрессию `make test`." % (
                          total, len(fe_rows) + (1 if smoke else 0),
                          " + smoke по всем разделам" if smoke else "", len(jtests), len(ptests)))

    doc.add_heading("3.1. Frontend (e2e, Playwright)", level=2)
    rows = []
    if smoke:
        rows.append(["TC-F000", "Smoke / Разделы",
                     "Рендер каждого из %d разделов NAV без ошибок консоли" % len(secs),
                     "e2e: section renders"])
    for i, (area, check) in enumerate(fe_rows, 1):
        rows.append(["TC-F%03d" % i, area, check, "e2e: run_e2e.py"])
    tbl(doc, ["ID", "Область", "Проверка", "Артефакт"], rows)

    doc.add_heading("3.2. Backend (Spring Boot + H2, MockMvc)", level=2)
    tbl(doc, ["ID", "Класс", "Проверка", "Метод"],
        [["TC-B%03d" % i, cls, purpose, mth + "()"] for i, (cls, mth, purpose) in enumerate(jtests, 1)])

    doc.add_heading("3.3. Analytics (Python)", level=2)
    tbl(doc, ["ID", "Файл", "Проверка"],
        [["TC-A%03d" % i, fn, purpose] for i, (fn, purpose) in enumerate(ptests, 1)])

    # 4. Матрица покрытия по блокам
    doc.add_heading("4. Матрица покрытия по блокам приложения", level=1)
    doc.add_paragraph("Разделы сгруппированы по 11 блокам меню. Каждый раздел покрыт smoke-проверкой рендера; "
                      "ключевые расчётные пути — отдельными e2e/backend-кейсами из раздела 3.")
    by_group = {}
    for _id, label, group in secs:
        by_group.setdefault(group, []).append(label)
    tbl(doc, ["Блок", "Разделов", "Разделы", "Покрытие"],
        [[g, len(items), ", ".join(items), "smoke-рендер + e2e"] for g, items in by_group.items()])

    # 5. Запуск
    doc.add_heading("5. Как запустить тесты", level=1)
    for line in ["make test — полная регрессия (frontend + backend + analytics);",
                 "make test-frontend / make test-java / make test-python — по слоям;",
                 "в песочнице backend — только mvn -o test (MockMvc); живой Tomcat не стартует;",
                 "CI прогоняет тот же набор на каждый push/PR; зелёная регрессия обязательна до merge."]:
        doc.add_paragraph(line, style="List Bullet")

    doc.add_paragraph().add_run(
        "Сгенерировано из набора тестов приложения «Управление кросс-функциональной командой» v%s (%s). "
        "Публикуется и обновляется при каждом релизе." % (VER, today)).italic = True
    doc.save(str(OUT))
    print("saved", OUT, OUT.stat().st_size, "bytes; e2e cases:", len(fe_rows), "+smoke" if smoke else "",
          "| backend:", len(jtests), "| analytics:", len(ptests), "| sections:", len(secs))


if __name__ == "__main__":
    main()
