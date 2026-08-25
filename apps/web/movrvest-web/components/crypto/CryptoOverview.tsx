/**
 * The crypto experience's investor-facing surface: hero, tabs and the
 * Overview widgets.
 *
 * Server components throughout — the tabs are plain links carrying a
 * `?view=` search parameter, so every view is URL-addressable, works
 * without JavaScript, and keyboard accessibility comes from the
 * anchor element itself. Everything rendered is a typed field the
 * backend composed; this file words nothing economic and computes
 * nothing analytical.
 */

import Link from "next/link";

import type { CryptoDossier } from "@/lib/api/crypto-dossier";
import {
  type CryptoView,
  type Development,
  type HeroModel,
  VIEW_LABELS,
  VIEWS,
  decisionModel,
  heroModel,
  keyFacts,
  keyRisks,
  latestDevelopments,
  watchNext,
  whyItMatters,
} from "@/components/crypto/overview-model";

const CARD = "rounded-2xl border border-slate-200 bg-white p-5";
const CARD_HEAD =
  "text-xs font-semibold uppercase tracking-[0.14em] text-slate-500";

/** The standing chip. Colour is never the only carrier: the words are. */
function StandingChip({ stated }: { stated: string }) {
  return (
    <span className="inline-flex items-center rounded-full border border-slate-300 px-2 py-0.5 text-[11px] font-medium text-slate-600">
      {stated}
    </span>
  );
}

// ── hero ────────────────────────────────────────────────────────────

export function CryptoHero({ hero }: { hero: HeroModel }) {
  return (
    <header className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold text-slate-950">
            {hero.symbol}
            {hero.name && hero.name !== hero.symbol ? (
              <span className="ml-3 text-lg font-normal text-slate-500">
                {hero.name}
              </span>
            ) : null}
          </h1>

          <p className="mt-1 text-sm font-medium text-slate-700">{hero.role}</p>
        </div>

        <div className="text-right">
          {hero.price?.stated ? (
            <>
              <p className="text-3xl font-semibold tabular-nums text-slate-950">
                {hero.price.stated}
              </p>

              <p className="mt-1 flex items-center justify-end gap-2 text-xs text-slate-500">
                <StandingChip stated={hero.price.standingStated} />
                {hero.price.age}
              </p>
            </>
          ) : (
            <p className="text-sm text-slate-500">No price is held.</p>
          )}
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-x-8 gap-y-3">
        {hero.returns.map((item) => (
          <div key={item.short}>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              {item.short}
            </p>
            <p className="text-lg font-semibold tabular-nums text-slate-800">
              {item.stated}
            </p>
          </div>
        ))}

        <div className="ml-auto text-right">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            MOVRvest course
          </p>
          <p className="text-lg font-semibold text-slate-950">{hero.state}</p>
          {hero.courseLine ? (
            <p className="text-xs text-slate-500">{hero.courseLine}</p>
          ) : null}
        </div>
      </div>
    </header>
  );
}

// ── tabs ────────────────────────────────────────────────────────────

export function CryptoTabs({
  symbol,
  current,
}: {
  symbol: string;
  current: CryptoView;
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
                ? `/crypto/${symbol}`
                : `/crypto/${symbol}?view=${view}`
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

// ── decision block ──────────────────────────────────────────────────

export function CryptoDecisionBlock({ dossier }: { dossier: CryptoDossier }) {
  const decision = decisionModel(dossier);

  return (
    <section aria-labelledby="crypto-course" className={CARD}>
      <h2 id="crypto-course" className={CARD_HEAD}>
        The current course
      </h2>

      <p className="mt-2 text-xl font-semibold text-slate-950">
        {decision.state}
        {decision.courseLine ? (
          <span className="ml-3 text-sm font-normal text-slate-500">
            {decision.courseLine}
          </span>
        ) : null}
      </p>

      <p className="mt-3 text-sm leading-6 text-slate-700">
        {decision.rationale}
      </p>

      {decision.unresolved.length > 0 ? (
        <div className="mt-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Unresolved — and what could change this view
          </h3>
          <ul className="mt-2 space-y-2">
            {decision.unresolved.map((item) => (
              <li key={item.stated} className="text-sm leading-6 text-slate-600">
                {item.stated}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {decision.boundary ? (
        <p className="mt-4 border-t border-slate-100 pt-3 text-xs leading-5 text-slate-500">
          {decision.boundary}
        </p>
      ) : null}
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
  items: readonly { stated: string; tag: string | null }[];
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
            {item.tag ? (
              <span className="ml-2 align-middle">
                <StandingChip stated={item.tag} />
              </span>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function CryptoSummaryRow({ dossier }: { dossier: CryptoDossier }) {
  const matters = whyItMatters(dossier);
  const risks = keyRisks(dossier);
  const watch = watchNext(dossier).map((item) => ({
    stated: item.stated,
    tag: null,
  }));

  if (matters.length === 0 && risks.length === 0 && watch.length === 0) {
    return null;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <SummaryCard id="crypto-why" title="Why it matters" items={matters} />
      <SummaryCard id="crypto-risks" title="Key risks" items={risks} />
      <SummaryCard id="crypto-watch" title="Watch next" items={watch} />
    </div>
  );
}

// ── key facts ───────────────────────────────────────────────────────

export function CryptoKeyFacts({ dossier }: { dossier: CryptoDossier }) {
  const facts = keyFacts(dossier);

  if (facts.length === 0) {
    return null;
  }

  return (
    <section aria-labelledby="crypto-facts" className={CARD}>
      <h2 id="crypto-facts" className={CARD_HEAD}>
        Key facts
      </h2>

      <dl className="mt-3 divide-y divide-slate-100">
        {facts.map((fact) => (
          <div
            key={`${fact.entity ?? ""}|${fact.label}`}
            className="flex flex-wrap items-baseline justify-between gap-x-4 py-2"
          >
            <dt className="text-sm text-slate-600">
              {fact.label}
              {fact.entity ? (
                <span className="ml-2 text-xs text-slate-400">
                  {fact.entity}
                </span>
              ) : null}
            </dt>

            <dd className="text-right">
              {fact.stated !== null ? (
                <span className="text-sm font-semibold tabular-nums text-slate-900">
                  {fact.stated}
                </span>
              ) : (
                <StandingChip stated={fact.standingStated} />
              )}

              <span className="ml-2 align-middle">
                {fact.stated !== null ? (
                  <StandingChip stated={fact.standingStated} />
                ) : null}
              </span>

              {fact.age ? (
                <p className="mt-0.5 text-[11px] text-slate-400">{fact.age}</p>
              ) : null}

              {fact.because ? (
                <p className="mt-1 max-w-sm text-xs leading-5 text-slate-500">
                  {fact.because}
                </p>
              ) : null}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

// ── latest developments ─────────────────────────────────────────────

function DevelopmentRow({ development }: { development: Development }) {
  return (
    <details className="group py-3">
      <summary className="flex cursor-pointer flex-wrap items-baseline gap-x-3 gap-y-1 text-sm">
        <span className="font-medium text-slate-900">
          {development.headline}
        </span>
        <StandingChip stated={development.category} />
        {development.age ? (
          <span className="text-xs text-slate-400">{development.age}</span>
        ) : null}
        <span className="text-xs text-slate-400">
          {development.verification}
        </span>
      </summary>

      {development.relevance ? (
        <p className="mt-2 text-sm leading-6 text-slate-600">
          {development.relevance}
        </p>
      ) : null}

      {development.accounts.length > 1 ? (
        <ul className="mt-2 space-y-1">
          {development.accounts.slice(1).map((account) => (
            <li key={account.stated} className="text-xs leading-5 text-slate-500">
              {account.stated}
              <span className="ml-1 text-slate-400">— {account.source}</span>
            </li>
          ))}
        </ul>
      ) : null}

      <p className="mt-2 text-[11px] text-slate-400">
        Sources: {development.sources.join(", ")}
      </p>
    </details>
  );
}

export function CryptoDevelopments({ dossier }: { dossier: CryptoDossier }) {
  const developments = latestDevelopments(dossier);

  if (developments.length === 0) {
    return null;
  }

  return (
    <section aria-labelledby="crypto-developments" className={CARD}>
      <h2 id="crypto-developments" className={CARD_HEAD}>
        Latest developments
      </h2>

      <div className="mt-1 divide-y divide-slate-100">
        {developments.map((development) => (
          <DevelopmentRow
            key={development.headline}
            development={development}
          />
        ))}
      </div>
    </section>
  );
}

// ── the Overview composition ────────────────────────────────────────

export function CryptoOverviewView({ dossier }: { dossier: CryptoDossier }) {
  return (
    <div className="mt-6 space-y-4">
      <CryptoDecisionBlock dossier={dossier} />
      <CryptoSummaryRow dossier={dossier} />

      <div className="grid gap-4 lg:grid-cols-2">
        <CryptoKeyFacts dossier={dossier} />
        <CryptoDevelopments dossier={dossier} />
      </div>
    </div>
  );
}
