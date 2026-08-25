/**
 * The stock dossier's investor-facing surface: hero, tabs, the course
 * and the Overview widgets.
 *
 * Server components throughout, and the tabs are plain links carrying a
 * `?view=` search parameter — the pattern #252 proved on the crypto
 * side, reused rather than reinvented: every view is URL-addressable,
 * works without JavaScript, and keyboard accessibility comes from the
 * anchor element. Everything rendered is a typed field the backend
 * composed; this file words nothing economic and computes nothing.
 *
 * Two components are deliberately *not* redefined here. `CourseEnvelope`
 * is the homepage's, so the capital consideration carries the same
 * constraints, liquidity limitation and disclaimer wherever it appears;
 * `TickerNews` is the existing paced surface with its own boundary.
 */

import Link from "next/link";

import { CourseEnvelope } from "@/components/executive/HomeSections";
import { StockQuoteRibbon } from "@/components/quote/FreshQuoteRibbon";
import type { CycleCourse } from "@/lib/api/cycle-review";
import type { DossierViewModel } from "@/lib/api/dossier";
import {
  type CapitalModel,
  type CourseModel,
  type DossierView,
  type HeroModel,
  type SnapshotFact,
  type SummaryItem,
  VIEW_LABELS,
  VIEWS,
  capitalModel,
  courseModel,
  heroModel,
  historyLine,
  snapshotModel,
  statedInstant,
  summaryWidgets,
} from "@/components/dossier/overview-model";

const CARD = "rounded-2xl border border-slate-200 bg-white p-5";
const CARD_HEAD =
  "text-xs font-semibold uppercase tracking-[0.14em] text-slate-500";

/** A neutral marker. One colour for every state: these vocabularies are
    not ordered, and colouring them would invent a ranking. */
function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-slate-300 px-2 py-0.5 text-[11px] font-medium text-slate-600">
      {children}
    </span>
  );
}

// ── hero ────────────────────────────────────────────────────────────

/**
 * The ticker, where it operates, when it was last reviewed, and what is
 * held of it.
 *
 * **No price, no company name, no return** — Stage 0 established that
 * no typed carrier serves any of the three to this route, and the
 * specification's instruction for that case is to omit and report.
 * Nothing borrows a name from a provider headline.
 *
 * **No conviction, no committee agreement, no "Evidence read: Yahoo
 * Finance", no score family and no narrative status.** The last of
 * those was a semantic defect rather than a matter of taste: it named
 * one provider quote reading in the hero of a dossier whose figures are
 * established from a 10-K, so the weaker claim borrowed the stronger's
 * authority. Its provenance still travels, per figure, in Financials.
 */
export function DossierHero({ hero }: { hero: HeroModel }) {
  return (
    <header className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-4">
        <div className="min-w-0">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
            {hero.symbol}
          </h1>

          {hero.industry ? (
            <p className="mt-1.5 text-sm text-slate-600">
              {hero.industry.label}
              {hero.industry.sector &&
              hero.industry.sector !== hero.industry.label ? (
                <span className="text-slate-400">
                  {" "}
                  · {hero.industry.sector}
                </span>
              ) : null}
              {hero.industry.age ? (
                <span className="ml-2 text-xs text-slate-400">
                  {hero.industry.age}
                </span>
              ) : null}
            </p>
          ) : null}
        </div>

        {/* A display quote on the provider's own clock, polled from
            this app's backend. Display only: the CIO review beside it
            keeps its own clock, and nothing decisive reads this. Where
            no quote stands the hero shows exactly what it showed
            before this existed — nothing. */}
        <StockQuoteRibbon symbol={hero.symbol} />

        <div className="text-right">
          {hero.reviewedAt ? (
            <>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                Last CIO review
              </p>
              <p className="text-sm font-medium text-slate-700">
                {hero.reviewedAt}
              </p>
            </>
          ) : null}

          {/* Read from the same completed cycle as the envelope, never
              from a fresh account call. A security that cycle did not
              hold shows nothing, which is not a zero. */}
          {hero.holding && hero.holding.weightPct !== null ? (
            <p className="mt-2 text-xs text-slate-500">
              Held at {hero.holding.weightPct.toFixed(2)}% of the account
            </p>
          ) : null}
        </div>
      </div>
    </header>
  );
}

// ── tabs ────────────────────────────────────────────────────────────

export function DossierTabs({
  symbol,
  current,
}: {
  symbol: string;
  current: DossierView;
}) {
  return (
    <nav
      aria-label="Dossier views"
      className="mt-6 flex gap-1 overflow-x-auto border-b border-slate-200"
    >
      {VIEWS.map((view) => {
        const active = view === current;

        return (
          <Link
            key={view}
            href={
              view === "overview"
                ? `/dossiers/${symbol}`
                : `/dossiers/${symbol}?view=${view}`
            }
            aria-current={active ? "page" : undefined}
            className={
              active
                ? "whitespace-nowrap border-b-2 border-slate-950 px-4 py-2.5 text-sm font-semibold text-slate-950"
                : "whitespace-nowrap border-b-2 border-transparent px-4 py-2.5 text-sm font-medium text-slate-500 hover:text-slate-950 focus-visible:text-slate-950"
            }
          >
            {VIEW_LABELS[view]}
          </Link>
        );
      })}
    </nav>
  );
}

// ── the course ──────────────────────────────────────────────────────

/**
 * What to consider doing, and why — the course primary, the disposition
 * secondary.
 *
 * The disposition is rendered beside the course as a label, never as
 * the thing itself: *"Consider adding to DIS"* is the answer to the
 * investor's question and `RECOMMEND` is the platform's name for it.
 * Where no action carrier exists the disposition stands alone with a
 * stated absence, because no word for an action can be derived from it.
 *
 * **No score comparison appears as the explanation.** `because` is the
 * decision's own sentence for this request.
 */
export function DossierCourseBlock({
  course,
  disposition,
  history,
}: {
  course: CourseModel | null;
  disposition: string;
  history: string | null;
}) {
  return (
    <section aria-labelledby="dossier-course" className={CARD}>
      <h2 id="dossier-course" className={CARD_HEAD}>
        The current course
      </h2>

      {course ? (
        <>
          <p className="mt-2 text-xl font-semibold leading-7 text-slate-950">
            {course.statement}
          </p>

          <p className="mt-1.5">
            <Chip>{course.disposition}</Chip>
          </p>

          <p className="mt-3 text-sm leading-6 text-slate-700">
            {course.because}
          </p>

          {course.checkpoint ? (
            <p className="mt-3 text-sm text-slate-600">
              <span className="font-semibold text-slate-800">Next: </span>
              {course.checkpoint}
            </p>
          ) : null}
        </>
      ) : (
        <>
          <p className="mt-2 text-xl font-semibold text-slate-950">
            {disposition}
          </p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            No course is recorded for this security. A disposition is not
            an action, and this platform will not word one from it.
          </p>
        </>
      )}

      {history ? (
        <p className="mt-4 border-t border-slate-100 pt-3 text-xs leading-5 text-slate-500">
          {history}
        </p>
      ) : null}
    </section>
  );
}

// ── capital consideration ───────────────────────────────────────────

/**
 * What the latest completed review allowed, in the domain's own
 * sentence — and only for the course it was decided for.
 *
 * Where the latest recorded allowance belongs to a different course
 * than the one displayed above, the envelope is withheld and the
 * withholding is stated in one sentence. No substitute envelope, no
 * recomputation, and no score or comparison mechanics: which facts
 * differed is the selector's business, not the reader's.
 */
export function DossierCapital({ capital }: { capital: CapitalModel | null }) {
  if (!capital) {
    return null;
  }

  if (capital.kind === "different_course") {
    return (
      <section aria-labelledby="dossier-capital" className={CARD}>
        <h2 id="dossier-capital" className={CARD_HEAD}>
          Capital allowance
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-600">
          No current capital allowance is shown because the latest recorded
          allowance belongs to a different course.
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby="dossier-capital" className={CARD}>
      <h2 id="dossier-capital" className={CARD_HEAD}>
        What the latest review allowed
      </h2>

      <p className="mt-2 text-xs leading-5 text-slate-500">
        From the CIO review completed {statedInstant(capital.finishedAt)}, which
        is where this consideration was decided. Nothing is recomputed here.
      </p>

      <div className="mt-3">
        <CourseEnvelope course={capital.course} />
      </div>
    </section>
  );
}

// ── the three summary widgets ───────────────────────────────────────

function SummaryCard({
  id,
  title,
  items,
}: {
  id: string;
  title: string;
  items: readonly SummaryItem[];
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section aria-labelledby={id} className={CARD}>
      <h2 id={id} className={CARD_HEAD}>
        {title}
      </h2>

      <ul className="mt-3 space-y-3">
        {items.map((item) => (
          <li key={item.stated} className="text-sm leading-6 text-slate-700">
            {item.stated}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function DossierSummaryRow({ dossier }: { dossier: DossierViewModel }) {
  // Computed together, so a statement claimed by one widget cannot
  // reappear under another heading.
  const { qualifies, wrong, changes } = summaryWidgets(dossier);

  if (
    qualifies.length === 0 &&
    wrong.length === 0 &&
    changes.length === 0
  ) {
    return null;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <SummaryCard
        id="dossier-qualifies"
        title="Why the case qualifies"
        items={qualifies}
      />
      <SummaryCard
        id="dossier-wrong"
        title="What could go wrong"
        items={wrong}
      />
      <SummaryCard
        id="dossier-changes"
        title="What changes the view"
        items={changes}
      />
    </div>
  );
}

// ── financial snapshot ──────────────────────────────────────────────

function SnapshotRow({ fact }: { fact: SnapshotFact }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-4 py-2">
      <dt className="text-sm text-slate-600">
        {fact.label}
        {fact.period ? (
          <span className="ml-2 text-xs text-slate-400">{fact.period}</span>
        ) : null}
      </dt>

      {/* The currency is already inside the figure — the shared
          formatter prefixes it for a currency-unit row — so it is not
          appended again here. Rendered twice it read "USD 16.99bnUSD". */}
      <dd className="flex shrink-0 items-baseline gap-2 text-right">
        <span className="text-sm font-semibold tabular-nums text-slate-900">
          {fact.stated}
        </span>

        <Chip>{fact.authority}</Chip>
      </dd>
    </div>
  );
}

/**
 * The figures already held, each under its honest authority.
 *
 * Filing evidence and a provider fallback sit in one list and stay
 * distinguishable, because the label travels on every row. The two
 * growth metrics keep the names the backend gave them, which is what
 * keeps them non-comparable: *"Revenue growth — FY filing"* and
 * *"Provider-reported revenue growth — period not stated"* are
 * different measurements, and no arithmetic between them is offered.
 *
 * What is not held is counted in one sentence rather than printed as a
 * column of empty cards.
 */
export function DossierSnapshot({ dossier }: { dossier: DossierViewModel }) {
  const snapshot = snapshotModel(dossier);

  if (snapshot.facts.length === 0 && !snapshot.coverage) {
    return null;
  }

  return (
    <section aria-labelledby="dossier-snapshot" className={CARD}>
      <h2 id="dossier-snapshot" className={CARD_HEAD}>
        Financial snapshot
      </h2>

      {snapshot.facts.length > 0 ? (
        <dl className="mt-3 divide-y divide-slate-100">
          {snapshot.facts.map((fact) => (
            <SnapshotRow key={fact.label} fact={fact} />
          ))}
        </dl>
      ) : null}

      {snapshot.coverage ? (
        <p className="mt-3 border-t border-slate-100 pt-3 text-xs leading-5 text-slate-500">
          {snapshot.coverage}
        </p>
      ) : null}
    </section>
  );
}

// ── the Overview composition ────────────────────────────────────────

/**
 * The default view, in the order the investor meets the questions.
 *
 * A responsive modular grid rather than one fixed layout: the course
 * and the capital consideration pair on a wide screen and stack on a
 * narrow one, and because the course is written first in the DOM it
 * stays first when they collapse.
 *
 * **The executive narrative is not here.** It is a client component
 * that fetches on mount, so leaving it out of this view is the whole
 * mechanism: the Overview issues no narrative request at all, and the
 * deterministic case never waits on a model. It renders under Thesis &
 * history, where the existing bounded path is invoked unchanged.
 */
export function DossierOverviewView({
  dossier,
  recorded,
  news,
}: {
  dossier: DossierViewModel;
  recorded: { course: CycleCourse; finishedAt: string } | null;
  news: React.ReactNode;
}) {
  const course = courseModel(dossier);
  const capital = capitalModel(dossier, recorded);

  return (
    <div className="mt-6 space-y-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <DossierCourseBlock
          course={course}
          disposition={dossier.decisionState}
          history={historyLine(dossier)}
        />
        <DossierCapital capital={capital} />
      </div>

      <DossierSummaryRow dossier={dossier} />

      <div className="grid gap-4 lg:grid-cols-2">
        <DossierSnapshot dossier={dossier} />
        {news}
      </div>
    </div>
  );
}

export { heroModel };
