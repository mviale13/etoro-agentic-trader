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

import { CryptoHeadlinePrice } from "@/components/quote/FreshQuoteRibbon";
import type { BriefView, CryptoDossier } from "@/lib/api/crypto-dossier";
import {
  type BriefBlock,
  type CryptoView,
  type Development,
  type HeroModel,
  VIEW_LABELS,
  VIEWS,
  briefBlocks,
  keyFacts,
  latestDevelopments,
  marketSetup,
} from "@/components/crypto/overview-model";

const CARD = "rounded-2xl border border-slate-200 bg-white p-4 sm:p-5";
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
    <header className="mt-6 rounded-3xl border border-slate-200 bg-white p-5 sm:p-8">
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

        {/* The headline price. Server-rendered with the established
            figure so the page waits on nothing; the ribbon's first
            successful poll replaces it with a current display quote on
            the provider's own clock. The established price and its
            methodology remain under Evidence untouched — this decides
            which figure leads, never what any figure means, and a
            display quote resolves no conflicted market value. Where no
            current quote and no established price exist, the state is
            stated: the investor needs the state, not an account of this
            platform's store. */}
        <CryptoHeadlinePrice
          symbol={hero.symbol}
          establishedStated={hero.price?.stated ?? null}
          establishedAge={hero.price?.age ?? null}
        />
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-x-8 gap-y-3">
        {hero.returns.map((item) => (
          <div key={item.short}>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              {item.short}
            </p>
            <p
              className={`text-lg font-semibold tabular-nums ${signedTone(item.stated)}`}
            >
              {item.stated}
            </p>
          </div>
        ))}

        <Exposure exposure={hero.exposure} />
      </div>

      {/* The course and what it means, stated once on the whole page.
          Both were previously rendered here *and* in the card below,
          so the investor read "INVESTIGATE — no capital action is
          suggested" twice before reaching a single finding. */}
      <div className="mt-5 border-t border-slate-100 pt-4">
        <div className="flex flex-wrap items-baseline gap-x-3">
          <p className="text-xl font-semibold text-slate-950">{hero.state}</p>
          {hero.courseLine ? (
            <p className="text-sm text-slate-500">— {hero.courseLine}</p>
          ) : null}
        </div>

        {/* One sentence: what holds up, set against what is not
            established. Composed by the CIO layer from quoted findings.
            Where it could not be composed, its own account of why. */}
        <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-700">
          {hero.setup ?? hero.setupAbsent}
        </p>
      </div>
    </header>
  );
}

/**
 * Signed colour, restrained: a leading sign carries it and nothing else.
 *
 * Keyed on the sign character the backend already wrote into the
 * figure, never on a number this side parsed — and never the only
 * carrier, since the sign is right there in the text.
 */
function signedTone(stated: string): string {
  if (stated.startsWith("+")) {
    return "text-emerald-700";
  }

  return stated.startsWith("-") ? "text-rose-700" : "text-slate-800";
}

/**
 * What the investor already owns, from the last completed cycle.
 *
 * Three states and they are not interchangeable: a recorded position,
 * a cycle that recorded the portfolio and did not contain this asset,
 * and no readable completed cycle at all. The middle one is a finding;
 * the last one is silence, and rendering either as "0%" would be a
 * number nobody measured.
 */
function Exposure({ exposure }: { exposure: HeroModel["exposure"] }) {
  if (exposure === null) {
    return null;
  }

  return (
    <div className="ml-auto text-right">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
        Your exposure
      </p>

      {exposure.held ? (
        <p className="text-lg font-semibold tabular-nums text-slate-800">
          {exposure.weightStated ?? "Share not computed"}
          {exposure.valueStated ? (
            <span className="ml-2 text-sm font-normal text-slate-500">
              {exposure.valueStated}
            </span>
          ) : null}
        </p>
      ) : (
        <p className="text-lg font-semibold text-slate-800">Not held</p>
      )}

      <p className="mt-0.5 max-w-xs text-[11px] leading-4 text-slate-400">
        {exposure.observed}
      </p>
    </div>
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

// ── the CIO brief ───────────────────────────────────────────────────

/**
 * The conclusion, in the order an investor asks for it.
 *
 * This replaced a card that led with *"what these conclusions are worth
 * to an investment case is not established by this platform"* — honest,
 * and a sentence about the platform where the reader needed a sentence
 * about the asset. That boundary has not been deleted; it moved to
 * Evidence, which is where audit material belongs.
 *
 * Three blocks, one surface, no card per block: dividers separate them,
 * because a box around each made three findings look like three
 * modules.
 */
function BriefColumn({ blocks }: { blocks: readonly BriefBlock[] }) {
  return (
    <section aria-labelledby="crypto-brief" className={CARD}>
      <h2 id="crypto-brief" className={CARD_HEAD}>
        MOVRvest brief
      </h2>

      <div className="mt-1 divide-y divide-slate-100">
        {blocks.map((block) => (
          <div key={block.id} className="py-3.5">
            <h3 className="text-sm font-semibold text-slate-950">
              {block.title}
            </h3>

            {block.lines.length > 0 ? (
              <ul className="mt-2 space-y-3">
                {block.lines.map((line) => (
                  <li key={`${line.owner}|${line.stated}`}>
                    <p className="text-sm leading-6 text-slate-700">
                      {line.stated}
                    </p>

                    {/* The owning layer's own qualification of its own
                        claim. It travels with the claim or not at all —
                        a précis may shorten a headline and may never
                        drop the sentence that limits it. */}
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      {line.qualification ? `${line.qualification} ` : ""}
                      <span className="text-slate-400">
                        {line.owner}
                        {line.support ? ` · ${line.support}` : ""}
                      </span>
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {block.absent}
              </p>
            )}

            {/* A capped list says what it is holding back. Silence here
                would let three findings read as all of them. */}
            {block.withheld > 0 ? (
              <p className="mt-2 text-[11px] text-slate-400">
                {block.withheld} further finding
                {block.withheld === 1 ? "" : "s"} under Evidence.
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}

// ── market setup ────────────────────────────────────────────────────

/**
 * Where the price is, over the windows this platform actually measures.
 *
 * Two things the brief asked for are **not held and are named as
 * absent**: where the price sits in a recent range, and whether volume
 * is normal. No high, no low and no baseline exists anywhere in the
 * payload, and deriving either from a 30-day return would be this
 * surface calculating — which it may not do. No conditional scenario is
 * worded here for the same reason: *"continuation would be better
 * supported if…"* is a forecast, and no layer beneath this one
 * establishes one.
 */
export function CryptoMarketSetup({ dossier }: { dossier: CryptoDossier }) {
  const setup = marketSetup(dossier);

  if (setup.returns.length === 0 && setup.volumeStated === null) {
    return null;
  }

  return (
    <section aria-labelledby="crypto-setup" className={CARD}>
      <h2 id="crypto-setup" className={CARD_HEAD}>
        Market setup
      </h2>

      {/* The price is not repeated here. The hero leads with it, and
          reprinting it under a second heading is the defect the course
          duplication already was — one fact, one place. */}
      <div className="mt-3 flex flex-wrap items-baseline gap-x-8 gap-y-3">
        {setup.returns.map((item) => (
          <div key={item.short}>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              {item.short}
            </p>
            <p
              className={`text-lg font-semibold tabular-nums ${signedTone(item.stated)}`}
            >
              {item.stated}
            </p>
          </div>
        ))}

        {setup.volumeStated ? (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              Reported volume, 24h
            </p>
            <p className="text-lg font-semibold tabular-nums text-slate-900">
              {setup.volumeStated}
            </p>
          </div>
        ) : null}
      </div>

      <ul className="mt-4 grid gap-x-8 gap-y-1 border-t border-slate-100 pt-3 lg:grid-cols-2">
        {setup.unavailable.map((stated) => (
          <li key={stated} className="text-xs leading-5 text-slate-500">
            {stated}
          </li>
        ))}
      </ul>
    </section>
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
            className="flex flex-wrap items-baseline justify-between gap-x-4 py-1.5"
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
              {/* Value, standing and provenance on one line. Stacked,
                  each row ran 81px on a phone and six of them made the
                  snapshot the tallest thing on the page after the
                  brief. Nothing was dropped to shrink it: the standing
                  and the source still travel with every figure. */}
              <span className="flex flex-wrap items-baseline justify-end gap-x-2">
                {fact.stated !== null ? (
                  <span className="text-sm font-semibold tabular-nums text-slate-900">
                    {fact.stated}
                  </span>
                ) : null}

                <StandingChip stated={fact.standingStated} />

                {fact.age ? (
                  <span className="text-[11px] text-slate-400">{fact.age}</span>
                ) : null}
              </span>

              {/* The source disagreement, one disclosure away.

                  Rendered inline this ran 343 and 414 characters for
                  HYPE's two conflicts — the full methodology account,
                  in a snapshot whose job is to say *not settled*. The
                  backend's sentence is unchanged and unparsed: no
                  shorter version of it is composed here, because
                  naming which sources disagree would mean reading
                  names out of prose. */}
              {fact.because ? (
                <details className="mt-1 text-left">
                  <summary className="cursor-pointer text-xs font-medium text-slate-500">
                    Why this is not settled
                  </summary>

                  <p className="mt-1 max-w-sm text-xs leading-5 text-slate-500">
                    {fact.because}
                  </p>
                </details>
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
    <details className="group py-2.5">
      <summary className="cursor-pointer text-sm">
        <span className="font-medium text-slate-900">
          {development.headline}
        </span>

        <span className="mt-1 flex flex-wrap items-baseline gap-x-2 text-xs text-slate-400">
          <StandingChip stated={development.category} />
          {development.age ? <span>{development.age}</span> : null}
          {/* Coverage, never verification: two outlets carrying one
              account are two reports of it and not a check on it. */}
          <span>{development.sourceCoverage}</span>
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

/**
 * The Overview explains the investment situation. The other tabs prove it.
 *
 * Reading order is the whole design, and it is the owner's: hero and
 * course, market setup, the brief, developments, then the metrics
 * snapshot with links onward. News is time-sensitive and used to sit
 * *beneath* a 1,362px facts block; metrics are reference and now sit
 * last.
 *
 * **Two columns, deliberately unequal.** "Why it matters", "Key risks"
 * and "Watch next" were three equal cards carrying very unequal
 * density, which gave them equal authority they had not earned. The
 * case is wide and reads first; what to watch, what happened and what
 * is held sit narrower beside it.
 *
 * **`items-start` is load-bearing.** The grid defaulted to
 * `align-items: normal`, so the short developments module stretched to
 * the facts module's 1,362px and the page carried a column of empty
 * white. Both columns now keep their natural height.
 */
export function CryptoOverviewView({
  dossier,
  brief,
}: {
  dossier: CryptoDossier;
  brief: BriefView;
}) {
  return (
    <div className="mt-6 space-y-3 sm:space-y-4">
      <CryptoMarketSetup dossier={dossier} />

      <div className="grid items-start gap-3 sm:gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <BriefColumn blocks={briefBlocks(brief)} />
        </div>

        <div className="space-y-3 sm:space-y-4">
          <CryptoDevelopments dossier={dossier} />
          <CryptoKeyFacts dossier={dossier} />
        </div>
      </div>

      <ProveIt symbol={dossier.symbol} />
    </div>
  );
}

/**
 * Where the evidence is, once the situation has been explained.
 *
 * Plain links rather than a card: the sixteen-row facts block was the
 * page's largest element and most of it belongs to Economics and
 * Tokenomics. Nothing was deleted, so the Overview says where it went.
 */
function ProveIt({ symbol }: { symbol: string }) {
  const links: readonly { view: CryptoView; stated: string }[] = [
    { view: "economics", stated: "All protocol and market metrics" },
    { view: "tokenomics", stated: "Supply, issuance and source comparisons" },
    { view: "evidence", stated: "Committees, questions and why MOVRvest stops here" },
  ];

  return (
    <nav
      aria-label="Evidence behind this view"
      className="flex flex-wrap gap-x-6 gap-y-1 px-1 pt-1"
    >
      {links.map((link) => (
        <Link
          key={link.view}
          href={`/crypto/${symbol}?view=${link.view}`}
          className="text-sm font-semibold text-slate-600 underline-offset-4 hover:text-slate-950 hover:underline"
        >
          {link.stated} →
        </Link>
      ))}
    </nav>
  );
}
