package com.planirovanie.service;

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
    private final TeamRepo team;
    private final TaskRepo tasks;
    private final ReleaseRepo releases;
    private final MilestoneRepo milestones;
    private final TechDebtRepo techDebt;
    private final RiskRepo risks;
    private final BugRepo bugs;
    private final HolidayRepo calendar;
    private final RetroRepo retro;
    private final RiceRepo rice;
    private final DependencyRepo deps;
    private final OkrRepo okr;

    public StateService(ParamRepo params, AppMetaRepo meta, DodRepo dod, TeamRepo team, TaskRepo tasks,
                        ReleaseRepo releases, MilestoneRepo milestones, TechDebtRepo techDebt, RiskRepo risks,
                        BugRepo bugs, HolidayRepo calendar, RetroRepo retro, RiceRepo rice, DependencyRepo deps,
                        OkrRepo okr) {
        this.params = params; this.meta = meta; this.dod = dod; this.team = team; this.tasks = tasks;
        this.releases = releases; this.milestones = milestones; this.techDebt = techDebt; this.risks = risks;
        this.bugs = bugs; this.calendar = calendar; this.retro = retro; this.rice = rice; this.deps = deps;
        this.okr = okr;
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
        s.team = team.findAllByOrderByOrdAsc();
        s.tasks = tasks.findAllByOrderByOrdAsc();
        s.releases = releases.findAllByOrderByOrdAsc();
        s.milestones = milestones.findAllByOrderByOrdAsc();
        s.techDebt = techDebt.findAllByOrderByOrdAsc();
        s.risks = risks.findAllByOrderByOrdAsc();
        s.bugs = bugs.findAllByOrderByOrdAsc();
        s.calendar = calendar.findAllByOrderByOrdAsc();
        s.retro = retro.findAllByOrderByOrdAsc();
        s.rice = rice.findAllByOrderByOrdAsc();
        s.deps = deps.findAllByOrderByOrdAsc();
        s.okr = okr.findAllByOrderByOrdAsc();
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
        order(s.team, (e, i) -> { e.id = null; e.ord = i; });
        order(s.tasks, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.releases, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.milestones, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.techDebt, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.risks, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.bugs, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.calendar, (e, i) -> { e.id = null; e.ord = i; });
        order(s.retro, (e, i) -> { e.id = null; e.ord = i; });
        order(s.rice, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.deps, (e, i) -> { e.pk = null; e.ord = i; });
        order(s.okr, (e, i) -> { e.id = null; e.ord = i; });

        dod.deleteAllInBatch();        if (s.dod != null)        dod.saveAll(s.dod);
        team.deleteAllInBatch();       if (s.team != null)       team.saveAll(s.team);
        tasks.deleteAllInBatch();      if (s.tasks != null)      tasks.saveAll(s.tasks);
        releases.deleteAllInBatch();   if (s.releases != null)   releases.saveAll(s.releases);
        milestones.deleteAllInBatch(); if (s.milestones != null) milestones.saveAll(s.milestones);
        techDebt.deleteAllInBatch();   if (s.techDebt != null)   techDebt.saveAll(s.techDebt);
        risks.deleteAllInBatch();      if (s.risks != null)      risks.saveAll(s.risks);
        bugs.deleteAllInBatch();       if (s.bugs != null)       bugs.saveAll(s.bugs);
        calendar.deleteAllInBatch();   if (s.calendar != null)   calendar.saveAll(s.calendar);
        retro.deleteAllInBatch();      if (s.retro != null)      retro.saveAll(s.retro);
        rice.deleteAllInBatch();       if (s.rice != null)       rice.saveAll(s.rice);
        deps.deleteAllInBatch();       if (s.deps != null)       deps.saveAll(s.deps);
        okr.deleteAllInBatch();        if (s.okr != null)        okr.saveAll(s.okr);

        m.version = current + 1;
        meta.save(m);
        return m.version;
    }
}
