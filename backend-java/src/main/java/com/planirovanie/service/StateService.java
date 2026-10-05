package com.planirovanie.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.planirovanie.dto.Dtos.*;
import com.planirovanie.entity.*;
import com.planirovanie.repo.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/** Assembles and persists the whole application state across all tables. */
@Service
public class StateService {

    private final ParamRepo params;
    private final AppMetaRepo meta;
    private final DodRepo dod;
    private final DorItemRepo dorItems;
    private final ScopeLogRepo scopeLog;
    private final ChangeRequestRepo changeRequests;
    private final IssueRepo issues;
    private final StakeholderRepo stakeholders;
    private final DecisionRepo decisions;
    private final ImpedimentRepo impediments;
    private final LessonRepo lessons;
    private final RaciRepo raci;
    private final StoryMapItemRepo storyMap;
    private final PokerRoundRepo poker;
    private final PortfolioProjectRepo portfolio;
    private final TeamRepo team;
    private final TaskRepo tasks;
    private final ReleaseRepo releases;
    private final MilestoneRepo milestones;
    private final TechDebtRepo techDebt;
    private final RiskRepo risks;
    private final BugRepo bugs;
    private final HolidayRepo calendar;
    private final RetroRepo retro;
    private final MoodRepo mood;
    private final SkillRepo skills;
    private final AgileMaturityRepo agile;
    private final KudosRepo kudos;
    private final ExperimentRepo experiments;
    private final RadarRepo radar;
    private final RiceRepo rice;
    private final MoscowRepo moscow;
    private final FaqRepo faq;
    private final GroomingRepo grooming;
    private final DemoRepo demo;
    private final DailyRepo daily;
    private final VacationRepo vacation;
    private final BirthdayRepo birthdays;
    private final DependencyRepo deps;
    private final OkrRepo okr;
    private final BoardRepo boards;
    private final BoardDocRepo boardDoc;
    private final SprintGoalRepo sprintGoals;
    private final WsjfRepo wsjf;
    private final ObjectMapper mapper = new ObjectMapper();

    public StateService(ParamRepo params, AppMetaRepo meta, DodRepo dod, TeamRepo team, TaskRepo tasks,
                        ReleaseRepo releases, MilestoneRepo milestones, TechDebtRepo techDebt, RiskRepo risks,
                        BugRepo bugs, HolidayRepo calendar, RetroRepo retro, MoodRepo mood, KudosRepo kudos,
                        ExperimentRepo experiments, RadarRepo radar, RiceRepo rice, MoscowRepo moscow,
                        FaqRepo faq, GroomingRepo grooming, DemoRepo demo, DailyRepo daily, VacationRepo vacation,
                        BirthdayRepo birthdays, DependencyRepo deps, OkrRepo okr, BoardRepo boards,
                        BoardDocRepo boardDoc, SkillRepo skills, AgileMaturityRepo agile,
                        SprintGoalRepo sprintGoals, WsjfRepo wsjf,
                        DorItemRepo dorItems, ScopeLogRepo scopeLog,
                        ChangeRequestRepo changeRequests, IssueRepo issues, StakeholderRepo stakeholders,
                        DecisionRepo decisions, ImpedimentRepo impediments, LessonRepo lessons,
                        RaciRepo raci, StoryMapItemRepo storyMap, PokerRoundRepo poker,
                        PortfolioProjectRepo portfolio) {
        this.params = params; this.meta = meta; this.dod = dod; this.team = team; this.tasks = tasks;
        this.releases = releases; this.milestones = milestones; this.techDebt = techDebt; this.risks = risks;
        this.bugs = bugs; this.calendar = calendar; this.retro = retro; this.mood = mood; this.kudos = kudos;
        this.experiments = experiments; this.radar = radar; this.rice = rice; this.moscow = moscow;
        this.faq = faq; this.grooming = grooming; this.demo = demo; this.daily = daily; this.vacation = vacation;
        this.birthdays = birthdays; this.deps = deps;
        this.okr = okr; this.boards = boards; this.boardDoc = boardDoc; this.skills = skills; this.agile = agile;
        this.sprintGoals = sprintGoals; this.wsjf = wsjf;
        this.dorItems = dorItems; this.scopeLog = scopeLog;
        this.changeRequests = changeRequests; this.issues = issues; this.stakeholders = stakeholders;
        this.decisions = decisions; this.impediments = impediments; this.lessons = lessons;
        this.raci = raci; this.storyMap = storyMap; this.poker = poker; this.portfolio = portfolio;
    }

    @Transactional(readOnly = true)
    public StateDto get() {
        StateDto s = new StateDto();
        Param p = params.findById(1).orElseGet(Param::new);
        ParamsDto pd = new ParamsDto();
        pd.name = p.name; pd.start = p.startDate; pd.sprintDays = p.sprintDays; pd.focus = p.focus;
        pd.today = p.todayDate; pd.goal = p.goal; pd.sprints = p.sprints;
        s.params = pd;
        BudgetDto bd = new BudgetDto();
        bd.rate = p.budgetRate; bd.total = p.budgetTotal;
        s.budget = bd;
        s.ttmTarget = p.ttmTarget;
        s.dod = dod.findAllByOrderByOrdAsc();
        s.dorItems = dorItems.findAllByOrderByOrdAsc();
        s.scopeLog = scopeLog.findAllByOrderByOrdAsc();
        s.team = team.findAllByOrderByOrdAsc();
        s.tasks = tasks.findAllByOrderByOrdAsc();
        s.releases = releases.findAllByOrderByOrdAsc();
        s.milestones = milestones.findAllByOrderByOrdAsc();
        s.techDebt = techDebt.findAllByOrderByOrdAsc();
        s.risks = risks.findAllByOrderByOrdAsc();
        s.bugs = bugs.findAllByOrderByOrdAsc();
        s.calendar = calendar.findAllByOrderByOrdAsc();
        s.retro = retro.findAllByOrderByOrdAsc();
        s.mood = mood.findAllByOrderByOrdAsc();
        s.skills = skills.findAllByOrderByOrdAsc();
        s.agile = agile.findAllByOrderByOrdAsc();
        s.sprintGoals = sprintGoals.findAllByOrderByOrdAsc();
        s.wsjf = wsjf.findAllByOrderByOrdAsc();
        s.kudos = kudos.findAllByOrderByOrdAsc();
        s.experiments = experiments.findAllByOrderByOrdAsc();
        s.radar = radar.findAllByOrderByOrdAsc();
        s.rice = rice.findAllByOrderByOrdAsc();
        s.moscow = moscow.findAllByOrderByOrdAsc();
        s.faq = faq.findAllByOrderByOrdAsc();
        s.grooming = grooming.findAllByOrderByOrdAsc();
        s.demo = demo.findAllByOrderByOrdAsc();
        s.daily = daily.findAllByOrderByOrdAsc();
        s.vacation = vacation.findAllByOrderByOrdAsc();
        s.birthdays = birthdays.findAllByOrderByOrdAsc();
        s.deps = deps.findAllByOrderByOrdAsc();
        s.okr = okr.findAllByOrderByOrdAsc();
        s.changeRequests = changeRequests.findAllByOrderByOrdAsc();
        s.issues = issues.findAllByOrderByOrdAsc();
        s.stakeholders = stakeholders.findAllByOrderByOrdAsc();
        s.decisions = decisions.findAllByOrderByOrdAsc();
        s.impediments = impediments.findAllByOrderByOrdAsc();
        s.lessons = lessons.findAllByOrderByOrdAsc();
        s.raci = raci.findAllByOrderByOrdAsc();
        s.storyMap = storyMap.findAllByOrderByOrdAsc();
        s.poker = poker.findAllByOrderByOrdAsc();
        s.portfolio = portfolio.findAllByOrderByOrdAsc();
        s.boards = boards.findAllByOrderByOrdAsc();
        boardDoc.findById(1).ifPresent(bdoc -> {
            if (bdoc.data != null && !bdoc.data.isBlank()) {
                try { s.board = mapper.readTree(bdoc.data); } catch (Exception ignore) {}
            }
        });
        return s;
    }

    @Transactional(readOnly = true)
    public long version() {
        return meta.findById(1).map(m -> m.version == null ? 1L : m.version).orElse(1L);
    }

    private static <T> void order(List<T> list, java.util.function.BiConsumer<T, Integer> setOrd) {
        if (list == null) return;
        for (int i = 0; i < list.size(); i++) setOrd.accept(list.get(i), i);
    }

    @Transactional
    public long replace(StateDto s, Long expectedVersion) {
        if (s == null) s = new StateDto();

        // Optimistic concurrency: lock the version row, reject stale writes before touching data.
        AppMeta m = meta.findForUpdate().orElseGet(() -> { AppMeta nm = new AppMeta(); nm.id = 1; nm.version = 0L; return nm; });
        long current = (m.version == null ? 0L : m.version);
        if (expectedVersion != null && expectedVersion.longValue() != current) {
            throw new VersionConflictException(current);
        }

        // params + budget + ttmTarget (single row, id = 1)
        Param p = params.findById(1).orElseGet(() -> { Param np = new Param(); np.id = 1; return np; });
        if (s.params != null) {
            p.name = s.params.name; p.startDate = s.params.start; p.sprintDays = s.params.sprintDays;
            p.focus = s.params.focus; p.todayDate = s.params.today; p.goal = s.params.goal; p.sprints = s.params.sprints;
        }
        if (s.budget != null) { p.budgetRate = s.budget.rate; p.budgetTotal = s.budget.total; }
        if (s.ttmTarget != null) p.ttmTarget = s.ttmTarget;
        params.save(p);

        order(s.dod, (e, i) -> { e.id = null; e.ord = i; });
        order(s.dorItems, (e, i) -> { e.id = null; e.ord = i; });
        order(s.scopeLog, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.team, (e, i) -> { e.id = null; e.ord = i; });
        order(s.tasks, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.releases, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.milestones, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.techDebt, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.risks, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.bugs, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.calendar, (e, i) -> { e.id = null; e.ord = i; });
        order(s.retro, (e, i) -> { e.id = null; e.ord = i; });
        order(s.mood, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.skills, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.agile, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.sprintGoals, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.wsjf, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.kudos, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.experiments, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.radar, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.rice, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.moscow, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.faq, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.grooming, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.demo, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.daily, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.vacation, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.birthdays, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.deps, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.okr, (e, i) -> { e.id = null; e.ord = i; });
        order(s.changeRequests, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.issues, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.stakeholders, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.decisions, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.impediments, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.lessons, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.raci, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.storyMap, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.poker, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.portfolio, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.boards, (e, i) -> { e.pk = null; e.ord = i; });

        dod.deleteAllInBatch();        if (s.dod != null)        dod.saveAll(s.dod);
        dorItems.deleteAllInBatch();   if (s.dorItems != null)   dorItems.saveAll(s.dorItems);
        scopeLog.deleteAllInBatch();   if (s.scopeLog != null)   scopeLog.saveAll(s.scopeLog);
        team.deleteAllInBatch();       if (s.team != null)       team.saveAll(s.team);
        tasks.deleteAllInBatch();      if (s.tasks != null)      tasks.saveAll(s.tasks);
        releases.deleteAllInBatch();   if (s.releases != null)   releases.saveAll(s.releases);
        milestones.deleteAllInBatch(); if (s.milestones != null) milestones.saveAll(s.milestones);
        techDebt.deleteAllInBatch();   if (s.techDebt != null)   techDebt.saveAll(s.techDebt);
        risks.deleteAllInBatch();      if (s.risks != null)      risks.saveAll(s.risks);
        bugs.deleteAllInBatch();       if (s.bugs != null)       bugs.saveAll(s.bugs);
        calendar.deleteAllInBatch();   if (s.calendar != null)   calendar.saveAll(s.calendar);
        retro.deleteAllInBatch();      if (s.retro != null)      retro.saveAll(s.retro);
        mood.deleteAllInBatch();       if (s.mood != null)       mood.saveAll(s.mood);
        skills.deleteAllInBatch();     if (s.skills != null)     skills.saveAll(s.skills);
        agile.deleteAllInBatch();      if (s.agile != null)      agile.saveAll(s.agile);
        sprintGoals.deleteAllInBatch();if (s.sprintGoals != null) sprintGoals.saveAll(s.sprintGoals);
        wsjf.deleteAllInBatch();       if (s.wsjf != null)       wsjf.saveAll(s.wsjf);
        kudos.deleteAllInBatch();      if (s.kudos != null)      kudos.saveAll(s.kudos);
        experiments.deleteAllInBatch();if (s.experiments != null) experiments.saveAll(s.experiments);
        radar.deleteAllInBatch();      if (s.radar != null)      radar.saveAll(s.radar);
        rice.deleteAllInBatch();       if (s.rice != null)       rice.saveAll(s.rice);
        moscow.deleteAllInBatch();     if (s.moscow != null)     moscow.saveAll(s.moscow);
        faq.deleteAllInBatch();        if (s.faq != null)        faq.saveAll(s.faq);
        grooming.deleteAllInBatch();   if (s.grooming != null)   grooming.saveAll(s.grooming);
        demo.deleteAllInBatch();       if (s.demo != null)       demo.saveAll(s.demo);
        daily.deleteAllInBatch();      if (s.daily != null)      daily.saveAll(s.daily);
        vacation.deleteAllInBatch();   if (s.vacation != null)   vacation.saveAll(s.vacation);
        birthdays.deleteAllInBatch();  if (s.birthdays != null)  birthdays.saveAll(s.birthdays);
        deps.deleteAllInBatch();       if (s.deps != null)       deps.saveAll(s.deps);
        okr.deleteAllInBatch();        if (s.okr != null)        okr.saveAll(s.okr);
        changeRequests.deleteAllInBatch(); if (s.changeRequests != null) changeRequests.saveAll(s.changeRequests);
        issues.deleteAllInBatch();     if (s.issues != null)     issues.saveAll(s.issues);
        stakeholders.deleteAllInBatch(); if (s.stakeholders != null) stakeholders.saveAll(s.stakeholders);
        decisions.deleteAllInBatch();  if (s.decisions != null)  decisions.saveAll(s.decisions);
        impediments.deleteAllInBatch(); if (s.impediments != null) impediments.saveAll(s.impediments);
        lessons.deleteAllInBatch();    if (s.lessons != null)    lessons.saveAll(s.lessons);
        raci.deleteAllInBatch();       if (s.raci != null)       raci.saveAll(s.raci);
        storyMap.deleteAllInBatch();   if (s.storyMap != null)   storyMap.saveAll(s.storyMap);
        poker.deleteAllInBatch();      if (s.poker != null)      poker.saveAll(s.poker);
        portfolio.deleteAllInBatch();  if (s.portfolio != null)  portfolio.saveAll(s.portfolio);
        boards.deleteAllInBatch();     if (s.boards != null)     boards.saveAll(s.boards);
        if (s.board != null && !s.board.isNull()) {
            BoardDoc bd = boardDoc.findById(1).orElseGet(() -> { BoardDoc nb = new BoardDoc(); nb.id = 1; return nb; });
            try { bd.data = mapper.writeValueAsString(s.board); } catch (Exception e) { bd.data = null; }
            boardDoc.save(bd);
        }

        m.version = current + 1;
        meta.save(m);
        return m.version;
    }
}
