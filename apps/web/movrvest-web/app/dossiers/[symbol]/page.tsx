import Link from "next/link";
import {
  ArrowLeft,
  ChevronDown,
  CircleAlert,
  Scale,
  ShieldAlert,
} from "lucide-react";

import { ExecutiveNarrative } from "@/components/executive/ExecutiveNarrative";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";
import { StatusPill } from "@/components/ui/StatusPill";
import { getDossier } from "@/lib/api/dossier";
import type {
  DossierAgreement,
  DossierAssetProfile,
  DossierClassification,
  DossierFundCost,
  DossierBusinessUnderstanding,
  DossierCommitteeOpinion,
  DossierCryptoMarket,
  DossierDecisionCourse,
  DossierSupply,
  DossierCryptoPlaybook,
  DossierFinancialUnderstanding,
  DossierMeasure,
  DossierPlaybook,
  DossierProtocolFundamentals,
  DossierDerivation,
  DossierScore,
  DossierSynthesis,
  DossierSynthesisFact,
  DossierTokenRating,
  DossierUnderstanding,
  DossierViewModel,
  TokenFactRow,
  CryptoQuestionView,
  MarketObservationView,
  SupplyFigureView,
  ValueChainView,
} from "@/lib/api/dossier";

export const dynamic = "force-dynamic";

type DossierPageProps = {
  params: Promise<{ symbol: string }>;
};

/**
 * The complete investment case for one security, in five questions:
 * what changed, why it matters, why it matters for this investor, what
 * the Artificial CIO recommends, and why the investor should trust it.
 *
 * Everything rendered here arrives from the backend dossier. This page
 * formats, groups and discloses; it computes nothing.
 */
export default async function DossierPage({ params }: DossierPageProps) {
  const { symbol } = await params;
  const normalizedSymbol = symbol.toUpperCase();

  const result = await getDossier(normalizedSymbol);

  return (
    <DashboardLayout>
      <PageIntegrity
        status={result.source === "backend" ? "live" : "placeholder"}
        endpoint={
          result.source === "backend"
            ? `/executive/${normalizedSymbol}/dossier`
            : undefined
        }
        description={
          result.source === "backend"
            ? "The decision, thesis, evidence, committee opinions and provenance are the Artificial CIO's own records. Absent measurements are shown as absent."
            : "Backend unreachable. Nothing is shown in its place."
        }
      />

      <main className="mx-auto w-full max-w-5xl px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-slate-950"
        >
          <ArrowLeft aria-hidden="true" className="size-4" />
          Overview
        </Link>

        {result.dossier ? (
          <Dossier dossier={result.dossier} />
        ) : (
          <Unavailable backendUrl={result.backendUrl} error={result.error} />
        )}
      </main>
    </DashboardLayout>
  );
}

function Unavailable({
  backendUrl,
  error,
}: {
  backendUrl: string;
  error?: string;
}) {
  return (
    <section className="mt-8 rounded-[28px] border border-amber-200 bg-amber-50 px-8 py-10">
      <h1 className="text-3xl font-semibold tracking-[-0.035em] text-amber-950">
        The backend is unreachable
      </h1>

      <p className="mt-4 max-w-2xl text-sm leading-6 text-amber-900">
        MOVRvest cannot currently read this investment case, so nothing is
        shown. No demo case stands in for a real one.
      </p>

      <p className="mt-6 text-sm text-amber-900">
        Tried:
        <code className="ml-2 rounded bg-white/70 px-1.5 py-0.5">
          {backendUrl}
        </code>
      </p>

      {error ? (
        <details className="mt-4 text-sm text-amber-900">
          <summary className="cursor-pointer font-semibold">
            Connection details
          </summary>

          <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs leading-5">
            {error}
          </pre>
        </details>
      ) : null}
    </section>
  );
}

/**
 * What kind of investment this is, and what that means for the analysis.
 *
 * The reason one dossier looks unlike another. A reader who cannot see
 * the framework cannot tell a question this platform declined to ask
 * from one it failed to answer — so coverage lists every analysis,
 * including the ones the playbook does not run, each with its reason.
 */
/**
 * The one reason every skipped analyst gives, where they all give it.
 *
 * Null as soon as they differ — then each analyst's own reason is the
 * only honest thing to print beside it.
 */
function sharedReason(playbook: DossierPlaybook): string | null {
  const skipped = playbook.coverage.filter((item) => !item.covered);

  if (skipped.length < 2 || skipped.length !== playbook.coverage.length) {
    return null;
  }

  const reasons = new Set(skipped.map((item) => item.reason ?? ""));

  const only = [...reasons][0];

  return reasons.size === 1 && only ? only : null;
}

/**
 * Somebody else's rating of this token, under their name.
 *
 * Where this platform's own analysts have nothing to read — a token
 * publishes no financial statements — a rater who publishes six
 * dimensions and a review date says more than an empty card does. It is
 * attributed and linked so the investor can check it, and it is
 * consumed by nothing: no score, no playbook, no decision.
 */
function TokenRating({ rating }: { rating: DossierTokenRating }) {
  const reviewed = rating.reviewedAt
    ? new Date(rating.reviewedAt).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "long",
        year: "numeric",
      })
    : null;

  return (
    <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          Third-party rating
        </p>

        <p className="text-xs text-slate-500">
          {rating.source}&apos;s opinion, not this platform&apos;s
        </p>
      </div>

      <div className="mt-3 flex flex-wrap items-baseline gap-3">
        <span className="text-3xl font-semibold tracking-[-0.03em] text-slate-950">
          {rating.level}
        </span>

        <span className="text-lg text-slate-600">
          {rating.score.toFixed(0)}/100
        </span>

        {/* The date the rating was reviewed, not the date it was read.
            A rating reviewed two years ago is a two-year-old opinion
            however recently it was fetched. */}
        {reviewed ? (
          <span className="text-sm text-slate-500">
            last reviewed {reviewed}
          </span>
        ) : null}
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {rating.dimensions.map((dimension) => (
          <div key={dimension.label}>
            <dt className="text-xs text-slate-500">{dimension.label}</dt>

            <dd className="mt-0.5 text-lg font-medium tabular-nums text-slate-900">
              {dimension.score.toFixed(0)}
            </dd>
          </div>
        ))}
      </dl>

      <p className="mt-5 text-xs leading-5 text-slate-500">
        Published by {rating.source} and shown as read. It is not evidence this
        platform gathered and reaches none of its scores or decisions.
        {rating.read ? ` Read ${rating.read.age}.` : ""}
      </p>

      {rating.pageUrl || rating.reportUrl ? (
        <p className="mt-2 flex flex-wrap gap-4 text-sm font-medium">
          {rating.pageUrl ? (
            <a
              className="text-slate-900 underline underline-offset-4"
              href={rating.pageUrl}
              rel="noreferrer noopener"
              target="_blank"
            >
              {rating.source} rating page
            </a>
          ) : null}

          {rating.reportUrl ? (
            <a
              className="text-slate-900 underline underline-offset-4"
              href={rating.reportUrl}
              rel="noreferrer noopener"
              target="_blank"
            >
              Full report
            </a>
          ) : null}
        </p>
      ) : null}
    </div>
  );
}

/**
 * Industry beside the earned investment playbook — two classifications,
 * two questions, rendered apart so neither substitutes for the other.
 *
 * Every visible sentence arrives from the backend: the industry's
 * standing (reported, none reported, never acquired), the playbook's
 * state (established, refused, unavailable) and the distinction between
 * the concepts. This side lays them out and classifies nothing — an
 * absence renders the backend's own words, never a default.
 */
function Classification({
  classification,
  heading,
}: {
  classification: DossierClassification;
  /** "Classification" on a company dossier — the backend's definition
      words it, this side only places it. */
  heading: string;
}) {
  const { industry, playbook } = classification;

  return (
    <section
      aria-labelledby="classification-heading"
      className="rounded-[28px] border border-slate-200 bg-white p-8"
    >
      <p
        id="classification-heading"
        className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500"
      >
        {heading}
      </p>

      <div className="mt-4 grid gap-8 sm:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Industry
          </p>

          <p className="mt-2 text-2xl font-semibold tracking-[-0.02em] text-slate-950">
            {industry.label}
          </p>

          {industry.sector ? (
            <p className="mt-1 text-sm text-slate-600">
              Sector: {industry.sector}
            </p>
          ) : null}

          <p className="mt-3 text-sm leading-6 text-slate-700">
            {industry.stated}
          </p>

          {/* `age` arrives already worded with its source ("Yahoo
              Finance, 3 days ago") — the backend's sentence, not
              recomposed here. */}
          {industry.read ? (
            <p className="mt-2 text-xs text-slate-500">
              {industry.read.age}
              {industry.read.lastKnown ? " — the most recent reading held" : ""}
            </p>
          ) : null}
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Investment playbook
          </p>

          {/* No pill and no colour on any state: the backend's label and
              sentence carry the whole claim, and a badge grading the
              states would rank an honest absence below a conclusion. */}
          <p className="mt-2 text-2xl font-semibold tracking-[-0.02em] text-slate-950">
            {playbook.label}
          </p>

          <p className="mt-3 text-sm leading-6 text-slate-700">
            {playbook.stated}
          </p>

          {playbook.narrowestAgreement ? (
            <p className="mt-2 text-xs text-slate-500">
              Rests on: {playbook.narrowestAgreement}
            </p>
          ) : null}
        </div>
      </div>

      <p className="mt-6 border-t border-slate-100 pt-4 text-xs leading-5 text-slate-500">
        {classification.distinction}
      </p>
    </section>
  );
}

function Playbook({
  playbook,
  rating,
  heading,
}: {
  playbook: DossierPlaybook;
  rating: DossierTokenRating | null;
  /** "How this security is analysed" on an equity, "Asset type" on a
      token — the backend's dossier definition words it, this side only
      places it. The analysis frame is not the earned classification;
      that renders in its own section above. */
  heading: string;
}) {
  return (
    <section
      aria-labelledby="playbook-heading"
      className="rounded-[28px] border border-slate-200 bg-white p-8"
    >
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        {heading}
      </p>

      <div className="mt-2 flex flex-wrap items-center gap-3">
        <h2
          id="playbook-heading"
          className="text-3xl font-semibold tracking-[-0.03em] text-slate-950"
        >
          {playbook.name}
        </h2>

        {/* Not classified is not a kind of company: it is the absence of
            evidence for one, and it is labelled rather than defaulted. */}
        {playbook.classified ? null : (
          <StatusPill status="partial" label="No industry reported" />
        )}
      </div>

      <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-700">
        {playbook.explanation}
      </p>

      {playbook.priorities.length > 0 ? (
        <div className="mt-6">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Analysed primarily for
          </p>

          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {playbook.priorities.map((item) => (
              <li
                key={item}
                className="flex gap-2.5 text-sm leading-6 text-slate-700"
              >
                <span
                  aria-hidden="true"
                  className="mt-2.5 size-1 shrink-0 rounded-full bg-slate-400"
                />

                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {playbook.coverage.length > 0 ? (
        <div className="mt-6 border-t border-slate-100 pt-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Playbook coverage
          </p>

          <ul className="mt-3 space-y-2">
            {playbook.coverage.map((item) => (
              <li key={item.analyst} className="flex gap-2.5 text-sm leading-6">
                <span
                  aria-hidden="true"
                  className={
                    item.covered ? "text-emerald-600" : "text-slate-300"
                  }
                >
                  {item.covered ? "✓" : "○"}
                </span>

                <span
                  className={item.covered ? "text-slate-800" : "text-slate-500"}
                >
                  {item.label}

                  {/* A reason every skipped analyst shares is printed once,
                      below. Four analysts each saying "a digital asset
                      publishes no financial statements" is one fact, told
                      four times, filling the card a token has least to
                      put in. */}
                  {item.reason && !sharedReason(playbook) ? (
                    <span className="block text-slate-500">
                      Not applicable — {item.reason}
                    </span>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>

          {sharedReason(playbook) ? (
            <p className="mt-3 text-sm leading-6 text-slate-500">
              None of them apply: {sharedReason(playbook)}
            </p>
          ) : null}
        </div>
      ) : null}

      {rating ? <TokenRating rating={rating} /> : null}
    </section>
  );
}

/**
 * The trust chip beside every asset-profile figure.
 *
 * Established, provider claim, MOVRvest-calculated, or absent — the
 * distinction the Zero Fake Numbers contract exists for. The words are
 * the backend's; this styles them so a claim can never borrow an
 * established fact's look.
 */
function StandingMark({ row }: { row: TokenFactRow }) {
  const styles: Record<string, string> = {
    established: "bg-slate-800 text-white",
    calculated: "bg-slate-200 text-slate-700",
    claimed: "bg-slate-100 text-slate-500",
    conflicted: "bg-amber-100 text-amber-800",
    rejected: "bg-amber-100 text-amber-800",
    absent: "bg-transparent text-slate-400",
  };

  return (
    <span
      className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
        styles[row.standing] ?? "bg-slate-100 text-slate-500"
      }`}
      title={row.because ?? undefined}
    >
      {row.standingStated}
    </span>
  );
}

/**
 * What is measured about this asset — with how far each figure can be
 * trusted, and the claims that failed validation kept in view.
 *
 * The crypto counterpart of the filing sections on a company dossier.
 * Everything is worded by the backend: values, standings, ages,
 * reasons, the rejection ledger. This groups and styles.
 */
function AssetProfile({
  profile,
  symbol,
}: {
  profile: DossierAssetProfile;
  symbol: string;
}) {
  return (
    <section aria-labelledby="asset-profile-heading">
      <SectionHeading id="asset-profile-heading">
        What is measured about this asset
      </SectionHeading>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
        Provider observations are dated and attributed, and served only as far
        as they survived validation. Rows marked MOVRvest-calculated are this
        platform&rsquo;s arithmetic over established figures — nothing here
        turns a one-day movement into a conclusion about {symbol}.
      </p>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        {profile.groups.map((group) => (
          <div
            key={group.title}
            className="rounded-2xl border border-slate-200 bg-white px-5 py-4"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
              {group.title}
            </p>

            <dl className="mt-3 space-y-2.5">
              {group.rows.map((row) => (
                <div key={row.label}>
                  <div className="flex items-baseline justify-between gap-3 text-sm">
                    <dt className="text-slate-700">{row.label}</dt>

                    <dd className="flex shrink-0 items-baseline gap-2">
                      <span
                        className={
                          row.stated === null
                            ? "text-slate-400"
                            : "font-semibold tabular-nums text-slate-800"
                        }
                      >
                        {row.stated ?? "unknown"}
                      </span>

                      <StandingMark row={row} />
                    </dd>
                  </div>

                  {/* The observation's attribution — the age line already
                      names its source — or, where no value is served, the
                      backend's account of why. */}
                  <p className="mt-0.5 text-xs leading-5 text-slate-400">
                    {row.stated === null
                      ? row.because
                      : (row.age ?? row.source)}
                  </p>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>

      {profile.rejected.length > 0 ? (
        <details className="mt-4 rounded-2xl border border-amber-200 bg-amber-50/60 px-5 py-4">
          <summary className="cursor-pointer text-sm font-semibold text-amber-900">
            Readings that failed validation ({profile.rejected.length})
          </summary>

          <p className="mt-2 text-xs leading-5 text-amber-800">
            Retained rather than discarded: a claim that was wrong is a fact
            about the source, and it is kept where it can be checked.
          </p>

          <ul className="mt-3 space-y-2 text-sm leading-6 text-amber-900">
            {profile.rejected.map((statement) => (
              <li key={statement}>{statement}</li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}

/**
 * The economics of the system behind a token — evidence, not verdicts.
 *
 * Deliberately free of adjectives. Nothing here is called strong, weak,
 * healthy, attractive or expensive: those are interpretations, and the
 * layer entitled to make them does not exist yet. What the investor
 * gets is what was measured, over which entity, by whom, when, under
 * whose definition — and, where a figure is absent, which of the five
 * kinds of absence it is.
 */
function ProtocolFundamentals({
  fundamentals,
  symbol,
}: {
  fundamentals: DossierProtocolFundamentals;
  symbol: string;
}) {
  if (fundamentals.entities.length === 0) {
    return (
      <section aria-labelledby="protocol-heading">
        <SectionHeading id="protocol-heading">
          The economics behind it
        </SectionHeading>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">
          {fundamentals.unmappedBecause}
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby="protocol-heading">
      <SectionHeading id="protocol-heading">
        The economics behind it
      </SectionHeading>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
        What the systems behind {symbol} earn, and who receives it — read from a
        source that publishes its own definitions, and shown beside the case
        rather than inside it. None of this reached the recommendation above,
        and nothing here is called strong or weak: the evidence comes before any
        reading of it.
      </p>

      <div className="mt-4 space-y-4">
        {fundamentals.entities.map((entity) => (
          <div
            key={entity.key}
            className="rounded-2xl border border-slate-200 bg-white px-5 py-4"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-sm font-semibold text-slate-800">
                {entity.name}
              </p>

              <span className="text-xs uppercase tracking-[0.15em] text-slate-400">
                {entity.kind}
              </span>
            </div>

            {/* Which entity generated the figures is part of the
                figures: the same name covers a venue and a chain whose
                fees differ by two orders of magnitude. */}
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Measures {entity.measures}.
            </p>

            {entity.mappingSettled ? null : (
              <p className="mt-2 text-xs leading-5 text-amber-700">
                {entity.mappingBasis}
              </p>
            )}

            <dl className="mt-4 space-y-2.5">
              {entity.facts.map((fact) => (
                <div key={fact.metric}>
                  <div className="flex items-baseline justify-between gap-3 text-sm">
                    <dt className="text-slate-700">
                      {fact.label}
                      {fact.window ? (
                        <span className="ml-1.5 text-xs text-slate-400">
                          over {fact.window}
                        </span>
                      ) : null}
                    </dt>

                    <dd className="flex shrink-0 items-baseline gap-2">
                      <span
                        className={
                          fact.stated === null
                            ? "text-slate-400"
                            : "font-semibold tabular-nums text-slate-800"
                        }
                      >
                        {fact.stated ?? "—"}
                      </span>

                      <span
                        className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                          fact.stated === null
                            ? "bg-transparent text-slate-400"
                            : "bg-slate-100 text-slate-500"
                        }`}
                        title={fact.because ?? undefined}
                      >
                        {fact.stated === null
                          ? fact.availabilityStated
                          : fact.standingStated}
                      </span>
                    </dd>
                  </div>

                  <p className="mt-0.5 text-xs leading-5 text-slate-400">
                    {fact.stated === null
                      ? fact.because
                      : (fact.age ?? fact.source)}
                  </p>

                  {/* The provider's own definition, verbatim. For a
                      value-accrual figure this sentence *is* the
                      mechanism — paraphrasing it would be inventing
                      one. */}
                  {fact.providerMethodology ? (
                    <p className="mt-1 border-l-2 border-slate-200 pl-3 text-xs leading-5 text-slate-500">
                      {fact.source} defines this as: {fact.providerMethodology}
                    </p>
                  ) : null}
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>

      {fundamentals.derived.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            MOVRvest arithmetic
          </p>

          <dl className="mt-3 space-y-3">
            {fundamentals.derived.map((figure) => (
              <div key={figure.label}>
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <dt className="text-slate-700">{figure.label}</dt>

                  <dd className="shrink-0 font-semibold tabular-nums text-slate-800">
                    {figure.statedValue}
                  </dd>
                </div>

                <p className="mt-0.5 text-xs leading-5 text-slate-500">
                  {figure.stated}
                </p>

                {/* Said every time it is shown: a run rate is not a
                    year that happened. */}
                <p className="mt-0.5 text-xs leading-5 text-amber-700">
                  {figure.caveat}
                </p>
              </div>
            ))}
          </dl>
        </div>
      ) : null}
    </section>
  );
}

/**
 * Which investment questions this kind of asset is asked at all.
 *
 * The section that answers a complaint the factor table could not: a
 * token dossier used to show the same four readings whether the subject
 * was Bitcoin or an exchange token, and an investor had no way to see
 * that one of them is not asked about protocol revenue *by design* while
 * the other's whole case turns on it.
 *
 * Three things are kept visibly apart here, because collapsing any two
 * is how a page starts lying. Whether a question applies is decided from
 * what kind of economic object this is, and from no figure at all.
 * Whether anything answers it is decided from the evidence, and from no
 * opinion of the question. And nothing on this page answers anything:
 * there is no verdict, no band and no score, and a question with
 * established evidence is not shown as better than one without.
 */
function CryptoPlaybook({
  playbook,
  symbol,
}: {
  playbook: DossierCryptoPlaybook;
  symbol: string;
}) {
  const asked = playbook.questions.filter(
    (question) =>
      question.cell === "ask" || question.cell === "ask_evidence_insufficient",
  );

  const declined = playbook.questions.filter(
    (question) => question.cell === "not_applicable",
  );

  const undetermined = playbook.questions.filter(
    (question) => question.cell === "undetermined",
  );

  return (
    <section aria-labelledby="crypto-playbook-heading">
      <SectionHeading id="crypto-playbook-heading">
        Which questions this asset is asked
      </SectionHeading>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
        What kind of economic object {symbol} is decides which investment
        questions are legitimate for it, and which would be the wrong
        instrument. That is settled before any figure is read, so a question
        this platform cannot answer never quietly becomes one it does not ask.
        Nothing here is an answer, and none of it reached the recommendation
        above.
      </p>

      <div className="mt-4 rounded-2xl border border-slate-200 bg-white px-5 py-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <p className="text-sm font-semibold text-slate-800">
            {playbook.name}
          </p>

          <span className="text-xs uppercase tracking-[0.15em] text-slate-400">
            {playbook.confidenceStated}
          </span>
        </div>

        <p className="mt-2 text-sm leading-6 text-slate-600">
          {playbook.explanation}
        </p>

        <p className="mt-3 text-xs leading-5 text-slate-500">
          {playbook.because}
        </p>

        {playbook.restsOn.length > 0 ? (
          <div className="mt-3">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">
              Rests on
            </p>

            <ul className="mt-1.5 space-y-1">
              {playbook.restsOn.map((line) => (
                <li key={line} className="text-xs leading-5 text-slate-500">
                  {line}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {/* A kind is not a verdict, and what the classification stops
            short of is stated where the classification is made. */}
        {playbook.doesNotEstablish.length > 0 ? (
          <div className="mt-3">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">
              Does not establish
            </p>

            <ul className="mt-1.5 space-y-1">
              {playbook.doesNotEstablish.map((line) => (
                <li key={line} className="text-xs leading-5 text-amber-700">
                  {line}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {playbook.alternatives.length > 0 ? (
          <div className="mt-3">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">
              Considered and not chosen
            </p>

            <ul className="mt-1.5 space-y-1">
              {playbook.alternatives.map((alternative) => (
                <li
                  key={alternative.archetype}
                  className="text-xs leading-5 text-slate-500"
                >
                  {alternative.notChosenBecause}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {/* Evidence held here and refused as a basis. A reader cannot
            otherwise tell a label that was rejected from one nobody had. */}
        {playbook.notClassifiedFrom.length > 0 ? (
          <div className="mt-3">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">
              Held here and not used to classify
            </p>

            <ul className="mt-1.5 space-y-1">
              {playbook.notClassifiedFrom.map((line) => (
                <li key={line} className="text-xs leading-5 text-slate-500">
                  {line}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="mt-3">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">
            Read through
          </p>

          <ul className="mt-1.5 space-y-1">
            {playbook.capabilities.map((capability) => (
              <li
                key={capability.key}
                className="text-xs leading-5 text-slate-500"
              >
                <span className="font-medium text-slate-600">
                  {capability.label}
                </span>{" "}
                — {capability.reads}
              </li>
            ))}
          </ul>
        </div>

        {/* Declared for a kind whose own questions this platform has not
            built. Saying so is what keeps it out of another kind's. */}
        {playbook.unmodelled.length > 0 ? (
          <div className="mt-3">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">
              Its own questions, not modelled here
            </p>

            <ul className="mt-1.5 space-y-1">
              {playbook.unmodelled.map((line) => (
                <li key={line} className="text-xs leading-5 text-amber-700">
                  {line}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>

      {asked.length > 0 ? (
        <div className="mt-4 space-y-3">
          {asked.map((question) => (
            <CryptoQuestion key={question.key} question={question} />
          ))}
        </div>
      ) : null}

      {undetermined.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Undetermined — {undetermined.length} questions
          </p>

          <p className="mt-2 text-xs leading-5 text-slate-500">
            {undetermined[0].applicabilityBecause}
          </p>

          <p className="mt-2 text-xs leading-5 text-slate-500">
            {undetermined.map((question) => question.label).join(" · ")}
          </p>
        </div>
      ) : null}

      {/* Declines are shown, never omitted. An omitted question and a
          refused one look identical to a reader, and they are opposite
          statements about the case. */}
      {declined.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Not asked of this kind of asset
          </p>

          <dl className="mt-3 space-y-3">
            {declined.map((question) => (
              <div key={question.key}>
                <dt className="text-sm text-slate-700">{question.label}</dt>

                <dd className="mt-0.5 text-xs leading-5 text-slate-500">
                  {question.applicabilityBecause}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}

      {playbook.chains.length > 0 ? (
        <div className="mt-6">
          <p className="text-sm font-semibold text-slate-800">
            Where the value goes
          </p>

          {/* One chain per economic entity and never one per security:
              Hyperliquid's venue and its chain are 224x apart on fees,
              and a figure from either substituted for the other would
              misstate the business by that factor. */}
          <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-500">
            One chain per economic system, never summed. The same word — fees —
            means a different thing at each ending, and only the source&apos;s
            own definition separates them.
          </p>

          <div className="mt-3 space-y-4">
            {playbook.chains.map((chain) => (
              <ValueChain key={chain.entity} chain={chain} />
            ))}
          </div>
        </div>
      ) : null}

      {playbook.unmappedBecause ? (
        <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-500">
          {playbook.unmappedBecause}
        </p>
      ) : null}
    </section>
  );
}

function CryptoQuestion({ question }: { question: CryptoQuestionView }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm font-semibold text-slate-800">{question.label}</p>

        {/* The joined reading, worded by the backend. "Ask — evidence
            insufficient" and "Not applicable" are different claims and
            are never rendered with the same word. */}
        <span
          className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-slate-100 text-slate-500"
          title={question.applicabilityBecause}
        >
          {question.cellStated}
        </span>
      </div>

      <p className="mt-1 text-sm leading-6 text-slate-600">{question.asks}</p>

      <p className="mt-1 text-xs leading-5 text-slate-400">
        {question.mattersBecause}
      </p>

      <dl className="mt-3 space-y-2">
        {question.evidence.map((item, index) => (
          <div key={`${question.key}-${index}`}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <dt className={item.met ? "text-slate-700" : "text-slate-400"}>
                {item.met ? item.demand : `Needs: ${item.demand}`}
              </dt>

              {item.met ? (
                <dd className="flex shrink-0 items-baseline gap-2">
                  <span className="font-semibold tabular-nums text-slate-800">
                    {item.stated ?? "—"}
                  </span>

                  <span
                    className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500"
                    title={item.because ?? undefined}
                  >
                    {item.standingStated}
                  </span>
                </dd>
              ) : null}
            </div>

            {item.met && (item.entity || item.age || item.source) ? (
              <p className="mt-0.5 text-xs leading-5 text-slate-400">
                {item.entity ? `${item.entity} — ` : ""}
                {item.age ?? item.source}
              </p>
            ) : null}
          </div>
        ))}
      </dl>
    </div>
  );
}

function ValueChain({ chain }: { chain: ValueChainView }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm font-semibold text-slate-800">{chain.entity}</p>

        <span className="text-xs uppercase tracking-[0.15em] text-slate-400">
          {chain.kind}
        </span>
      </div>

      <p className="mt-1 text-xs leading-5 text-slate-500">
        Measures {chain.measures}.
      </p>

      <dl className="mt-3 space-y-2.5">
        {chain.links.map((link) => (
          <div key={link.stage}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <dt className="text-slate-700">
                {link.label}
                {link.window ? (
                  <span className="ml-1.5 text-xs text-slate-400">
                    over {link.window}
                  </span>
                ) : null}
              </dt>

              <dd className="flex shrink-0 items-baseline gap-2">
                <span
                  className={
                    link.stated === null
                      ? "text-slate-400"
                      : "font-semibold tabular-nums text-slate-800"
                  }
                >
                  {link.stated ?? "—"}
                </span>

                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                    link.stated === null
                      ? "bg-transparent text-slate-400"
                      : "bg-slate-100 text-slate-500"
                  }`}
                  title={link.because ?? undefined}
                >
                  {link.stated === null
                    ? link.availabilityStated
                    : link.standingStated}
                </span>
              </dd>
            </div>

            {/* The source's own definition, verbatim. For the last stage
                this sentence *is* the mechanism, and paraphrasing it
                would be this platform inventing one. */}
            {link.methodology ? (
              <p className="mt-1 border-l-2 border-slate-200 pl-3 text-xs leading-5 text-slate-500">
                {link.methodology}
              </p>
            ) : null}
          </div>
        ))}
      </dl>

      <div className="mt-3 border-t border-slate-100 pt-3">
        <p className="text-sm text-slate-700">
          Reaching the token:{" "}
          <span className="font-semibold">{chain.mechanismStated}</span>
        </p>

        <p className="mt-1 text-xs leading-5 text-slate-500">{chain.because}</p>

        {chain.mappingSettled ? null : (
          <p className="mt-1 text-xs leading-5 text-amber-700">
            What this system&apos;s economics mean for the token is not settled.
          </p>
        )}
      </div>
    </div>
  );
}

/**
 * What kind of crypto market this asset is trading inside.
 *
 * Deliberately its own section, below the asset's own evidence and
 * outside every score on the page. The whole point of the boundary is
 * that an investor can tell "this asset is weakening" from "crypto
 * broadly is weakening", and a card that mixed the two would destroy
 * exactly the distinction it exists to make.
 *
 * Three readings sit side by side and are never merged: the market, the
 * peer group, and the asset's own return. The differences between them
 * are arithmetic, stated in percentage points and wearing no adjective —
 * no traffic light, no band, no regime label. A token that fell less
 * than its peers is not thereby a better asset, and nothing here says
 * it is.
 */
function CryptoMarketContext({
  context,
  symbol,
}: {
  context: DossierCryptoMarket;
  symbol: string;
}) {
  if (context.unavailableBecause) {
    return (
      <section aria-labelledby="crypto-market-heading">
        <SectionHeading id="crypto-market-heading">
          Crypto market context
        </SectionHeading>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">
          {context.unavailableBecause}
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby="crypto-market-heading">
      <SectionHeading id="crypto-market-heading">
        Crypto market context
      </SectionHeading>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
        The environment {symbol} trades inside, and its place in it. This is
        context and not quality: none of it reached the recommendation above,
        and a token that fell less than its peers is not thereby a better asset.
        Every figure is one provider&apos;s claim — a total market
        capitalisation is not independently reproducible, because the universe
        is the vendor&apos;s own.
      </p>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="text-sm font-semibold text-slate-800">
              Crypto market
            </p>

            <span className="text-xs text-slate-400">
              {context.marketAge ?? context.marketSource}
            </span>
          </div>

          <dl className="mt-3 space-y-2">
            {context.market.map((item) => (
              <MarketRow key={`${item.metric}-${item.interval}`} item={item} />
            ))}
          </dl>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
          <p className="text-sm font-semibold text-slate-800">
            {symbol} — its own returns
          </p>

          <dl className="mt-3 space-y-2">
            {context.returns.map((item) => (
              <MarketRow key={`${item.metric}-${item.interval}`} item={item} />
            ))}
          </dl>

          {/* An interval with a return and no comparator is a gap in the
              comparator, not an asset that did not move. */}
          {context.uncompared.length > 0 ? (
            <p className="mt-3 text-xs leading-5 text-slate-400">
              No comparator was published at {context.uncompared.join(", ")}:
              the provider reports asset returns at four intervals and market
              and category figures at one, so 24 hours is the only window where
              a difference means anything.
            </p>
          ) : null}
        </div>
      </div>

      {/* The peer group is a vendor's category under the vendor's name.
          It is not the analytical archetype above it, and the page says
          so where a reader would otherwise assume they agree. */}
      <div className="mt-4 rounded-2xl border border-slate-200 bg-white px-5 py-4">
        {context.peer ? (
          <>
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-sm font-semibold text-slate-800">
                Peer group — {context.peer.name}
              </p>

              <span className="text-xs uppercase tracking-[0.15em] text-slate-400">
                {context.peer.provider}&apos;s category
              </span>
            </div>

            <p className="mt-1 text-xs leading-5 text-slate-500">
              Selected because {context.peer.selectedBecause}
            </p>

            {context.peer.caveats.map((caveat) => (
              <p key={caveat} className="mt-2 text-xs leading-5 text-amber-700">
                {caveat}
              </p>
            ))}

            {context.peerObservations.length > 0 ? (
              <dl className="mt-3 space-y-2">
                {context.peerObservations.map((item) => (
                  <MarketRow
                    key={`${item.metric}-${item.interval}`}
                    item={item}
                  />
                ))}
              </dl>
            ) : null}
          </>
        ) : (
          <>
            <p className="text-sm font-semibold text-slate-800">
              Peer group — none
            </p>

            {/* A fake comparison would put a number on the page that
                reads like a measurement. The reason is shown instead. */}
            <p className="mt-1 text-xs leading-5 text-slate-500">
              {context.peerUnavailableBecause}
            </p>
          </>
        )}

        {context.considered.length > 0 ? (
          <div className="mt-3">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">
              Considered and not used
            </p>

            <ul className="mt-1.5 space-y-1">
              {context.considered.map((item) => (
                <li
                  key={item.name}
                  className="text-xs leading-5 text-slate-500"
                >
                  <span className="font-medium text-slate-600">
                    {item.name}
                  </span>{" "}
                  — {item.rejectedBecause}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>

      {context.relative.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Relative performance — MOVRvest arithmetic
          </p>

          <dl className="mt-3 space-y-3">
            {context.relative.map((item) => (
              <div key={`${item.comparator}-${item.interval}`}>
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <dt className="text-slate-700">
                    Against {item.comparator}
                    <span className="ml-1.5 text-xs text-slate-400">
                      over {item.interval}
                    </span>
                  </dt>

                  {/* No colour: a difference in percentage points is a
                      measurement, and shading it green or red would be
                      a verdict this platform has not earned. */}
                  <dd className="shrink-0 font-semibold tabular-nums text-slate-800">
                    {item.delta}
                  </dd>
                </div>

                <p className="mt-0.5 text-xs leading-5 text-slate-500">
                  {item.stated}
                </p>

                {item.caveat ? (
                  <p className="mt-0.5 text-xs leading-5 text-amber-700">
                    {item.caveat}
                  </p>
                ) : null}
              </div>
            ))}
          </dl>

          {context.concentrations.length > 0 ? (
            <div className="mt-4 border-t border-slate-200 pt-3">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
                How much of each comparator this asset is
              </p>

              <ul className="mt-1.5 space-y-1">
                {context.concentrations.map((item) => (
                  <li
                    key={item.comparator}
                    className="text-xs leading-5 text-slate-500"
                  >
                    {item.stated}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function MarketRow({ item }: { item: MarketObservationView }) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3 text-sm">
        <dt className="text-slate-700">
          {item.label}
          {item.interval === "instant" ? null : (
            <span className="ml-1.5 text-xs text-slate-400">
              over {item.interval}
            </span>
          )}
        </dt>

        <dd className="flex shrink-0 items-baseline gap-2">
          <span
            className={
              item.stated === null
                ? "text-slate-400"
                : "font-semibold tabular-nums text-slate-800"
            }
          >
            {item.stated ?? "—"}
          </span>

          {/* Every figure here is one provider's claim, and the label
              says so rather than letting a number look established. */}
          <span
            className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500"
            title={item.because ?? undefined}
          >
            {item.standingStated}
          </span>
        </dd>
      </div>

      {/* An aggregate is an aggregate of something, and which assets
          were counted is part of the number. */}
      {item.derived && item.universe ? (
        <p className="mt-0.5 text-xs leading-5 text-slate-400">
          MOVRvest&apos;s arithmetic over {item.universe}
        </p>
      ) : null}
    </div>
  );
}

/**
 * What each of this token's supply numbers actually counts.
 *
 * The section exists because "sources conflict" was hiding three
 * correct readings of the same ledger. Cardano publishes four
 * distinguishable quantities and three vendors were each reporting one
 * of them, to within a rounding error — so the numbers differed, and
 * nothing was wrong except the label they shared.
 *
 * What is rendered is therefore the vocabulary, in investor language:
 * what can ever exist, what exists now, what is still to come, and what
 * each party holds to be available. The provenance sits underneath.
 *
 * Nothing here is interpreted. Whether a supply structure is dilutive,
 * attractive or a risk is a reading this platform has not earned, and
 * no word on this card implies one.
 */
function Supply({ supply, symbol }: { supply: DossierSupply; symbol: string }) {
  if (supply.unavailableBecause) {
    return (
      <section aria-labelledby="supply-heading">
        <SectionHeading id="supply-heading">Supply</SectionHeading>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">
          {supply.unavailableBecause}
        </p>
      </section>
    );
  }

  const groups = supply.figures.reduce<Map<string, SupplyFigureView[]>>(
    (found, figure) => {
      const rows = found.get(figure.conceptStated) ?? [];

      rows.push(figure);
      found.set(figure.conceptStated, rows);

      return found;
    },
    new Map(),
  );

  const coexisting = supply.comparisons.filter(
    (item) => item.verdict === "coexist",
  );

  const conflicts = supply.comparisons.filter(
    (item) => item.verdict === "conflicted",
  );

  return (
    <section aria-labelledby="supply-heading">
      <SectionHeading id="supply-heading">Supply</SectionHeading>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
        Crypto supply is an accounting vocabulary rather than one number. Below
        is what each figure for {symbol} actually counts and whose definition
        decided it — because two numbers only disagree if they claim to
        represent the same thing.
      </p>

      {/* The headline an investor can act on: whether the estimates
          differ for a reason anybody has published. Far more useful
          than a bare "sources conflict". */}
      <p
        className={`mt-3 max-w-3xl text-sm leading-6 ${
          supply.methodologyDisagreement ? "text-amber-700" : "text-slate-600"
        }`}
      >
        {supply.methodologyDisagreement
          ? `Circulating-supply estimates for ${symbol} differ, and at least one party does not publish which token buckets it excludes. The figures below are shown as what each one counts.`
          : conflicts.length > 0
            ? `The circulating-supply estimates for ${symbol} either agree or count different, stated quantities. One figure below still disagrees with the chain, and it is not about what circulates.`
            : `Every figure below either agrees with the others or counts a different, stated quantity. Nothing about ${symbol}'s supply is in dispute.`}
      </p>

      <div className="mt-4 space-y-4">
        {[...groups.entries()].map(([concept, figures]) => (
          <div
            key={concept}
            className="rounded-2xl border border-slate-200 bg-white px-5 py-4"
          >
            <p className="text-sm font-semibold text-slate-800">{concept}</p>

            <dl className="mt-3 space-y-3">
              {figures.map((figure, index) => (
                <div key={`${figure.source}-${figure.reportedAs}-${index}`}>
                  <div className="flex items-baseline justify-between gap-3 text-sm">
                    <dt className="text-slate-700">
                      {figure.source}
                      {figure.reportedAs ? (
                        <span className="ml-1.5 text-xs text-slate-400">
                          as {figure.reportedAs}
                        </span>
                      ) : null}
                    </dt>

                    <dd className="flex shrink-0 items-baseline gap-2">
                      <span className="font-semibold tabular-nums text-slate-800">
                        {figure.stated}
                      </span>

                      <span
                        className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500"
                        title={figure.authorityStated}
                      >
                        {figure.standingStated}
                      </span>
                    </dd>
                  </div>

                  {/* The methodology is part of the fact: a circulating
                      figure without it cannot be compared with anything. */}
                  <p className="mt-0.5 text-xs leading-5 text-slate-500">
                    {figure.definedBy}: {figure.methodology}
                    {figure.disclosed ? null : " — not published"}
                  </p>

                  {figure.excludes.length > 0 ? (
                    <p className="mt-0.5 text-xs leading-5 text-slate-400">
                      Excludes {figure.excludes.join("; ")}
                    </p>
                  ) : null}

                  {figure.caveats.map((caveat) => (
                    <p
                      key={caveat}
                      className="mt-1 text-xs leading-5 text-amber-700"
                    >
                      {caveat}
                    </p>
                  ))}
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>

      {/* Coexistence is the finding, so it is shown before the
          conflicts: these numbers differ and both are right. */}
      {coexisting.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Different numbers, both correct
          </p>

          <ul className="mt-2 space-y-2">
            {coexisting.map((item, index) => (
              <li
                key={`${item.leftSource}-${item.rightSource}-${index}`}
                className="text-xs leading-5 text-slate-600"
              >
                {item.because}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {conflicts.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Genuine disagreements
          </p>

          <ul className="mt-2 space-y-2">
            {conflicts.map((item, index) => (
              <li
                key={`${item.leftSource}-${item.rightSource}-${index}`}
                className="text-xs leading-5 text-slate-600"
              >
                <span className="font-medium text-slate-700">
                  {item.leftSource} {item.leftStated} · {item.rightSource}{" "}
                  {item.rightStated}
                </span>{" "}
                — {item.because}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {supply.unresolved.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">
            Unresolved
          </p>

          <ul className="mt-1.5 space-y-1">
            {supply.unresolved.map((line) => (
              <li key={line} className="text-xs leading-5 text-slate-500">
                {line}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function Dossier({ dossier }: { dossier: DossierViewModel }) {
  return (
    <div className="mt-8 space-y-10">
      {/* A token's analysis lives on its own surface, because a token is
          not a company with different labels: the conviction, the score
          and the committee agreement below are the equity case, and none
          of the crypto evidence reaches them. Linked rather than
          redirected while both exist. */}
      {dossier.definition.kind === "crypto" ? (
        <Link
          href={`/crypto/${dossier.symbol}`}
          className="flex items-center justify-between rounded-[20px] border border-slate-200 bg-white px-5 py-4 hover:border-slate-400"
        >
          <span className="text-sm text-slate-700">
            <span className="font-semibold text-slate-900">
              Open the digital-asset dossier
            </span>{" "}
            — the archetype, what can usefully be said, both committees, supply
            semantics and what is happening.
          </span>
          <span aria-hidden="true" className="text-slate-400">
            &rarr;
          </span>
        </Link>
      ) : null}

      <DecisionHeader dossier={dossier} />

      {dossier.securityEvidenced ? null : <UnevidencedNotice />}

      {/* Asked for from the browser once this page is readable. The
          case above does not wait on it and does not depend on it. */}
      <ExecutiveNarrative symbol={dossier.symbol} />

      {dossier.classification ? (
        <Classification
          classification={dossier.classification}
          heading={dossier.definition.classificationHeading}
        />
      ) : null}

      {dossier.playbook ? (
        <Playbook
          playbook={dossier.playbook}
          rating={dossier.tokenRating}
          heading={dossier.definition.analysisHeading}
        />
      ) : null}

      {dossier.fundCost ? <FundCost cost={dossier.fundCost} /> : null}

      {dossier.assetProfile ? (
        <AssetProfile profile={dossier.assetProfile} symbol={dossier.symbol} />
      ) : null}

      {dossier.protocolFundamentals ? (
        <ProtocolFundamentals
          fundamentals={dossier.protocolFundamentals}
          symbol={dossier.symbol}
        />
      ) : null}

      {dossier.cryptoPlaybook ? (
        <CryptoPlaybook
          playbook={dossier.cryptoPlaybook}
          symbol={dossier.symbol}
        />
      ) : null}

      {dossier.supply ? (
        <Supply supply={dossier.supply} symbol={dossier.symbol} />
      ) : null}

      {dossier.cryptoMarket ? (
        <CryptoMarketContext
          context={dossier.cryptoMarket}
          symbol={dossier.symbol}
        />
      ) : null}

      <WhatChanged dossier={dossier} />
      <Recommendation dossier={dossier} />
      <InvestorContext dossier={dossier} />

      {dossier.understanding ? (
        <Understanding
          understanding={dossier.understanding}
          symbol={dossier.symbol}
        />
      ) : null}

      <WhyTrustThis dossier={dossier} />
    </div>
  );
}

/**
 * What this platform has read out of the company's own filing.
 *
 * Placed beside the case rather than inside it, and labelled so, because
 * none of it reached the recommendation above: no analyst consumes an
 * understanding, and the decision would be identical if this section
 * were removed. It is here so an investor can see the filing-grade facts
 * the platform holds — and, just as much, the ones it does not.
 *
 * Every claim carries how firmly it is known, next to the claim. A
 * business that earns three ways where one of those rests on three
 * readings out of five is a different finding from one where all five
 * agreed, and a surface that showed only the first half would be the
 * confident-sounding page this platform exists to avoid.
 */
function Understanding({
  understanding,
  symbol,
}: {
  understanding: DossierUnderstanding;
  symbol: string;
}) {
  return (
    <section aria-labelledby="understanding-heading">
      <SectionHeading id="understanding-heading">
        What its own filing establishes
      </SectionHeading>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
        Read from {symbol}&rsquo;s own published accounts, and shown beside the
        case rather than inside it — none of this reached the recommendation
        above. Each claim carries the readings that agreed on it.
      </p>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <BusinessUnderstandingCard
          business={understanding.business}
          absent={understanding.businessAbsentBecause}
        />

        <FinancialUnderstandingCard
          financial={understanding.financial}
          absent={understanding.financialAbsentBecause}
        />
      </div>
    </section>
  );
}

/** How firmly a claim is held, in the readings' own counts. */
function Width({ agreement }: { agreement: DossierAgreement | null }) {
  if (agreement === null) {
    return null;
  }

  return (
    <span
      className={
        agreement.settled
          ? "shrink-0 text-xs tabular-nums text-slate-400"
          : "shrink-0 text-xs font-semibold tabular-nums text-amber-700"
      }
      title={
        agreement.settled
          ? "Every reading that addressed this agreed."
          : "Some readings disagreed. The claim is served at this width, not as settled."
      }
    >
      {agreement.agreeing}/{agreement.readings}
    </span>
  );
}

/** A card that says what is missing and why, and substitutes nothing. */
function NotRead({ title, reason }: { title: string; reason: string | null }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
      <p className="text-sm font-semibold text-slate-800">{title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-500">
        {reason ?? "Nothing has been read for this security."}
      </p>
    </div>
  );
}

function Quorum({
  quorate,
  count,
  quorum,
}: {
  quorate: boolean;
  count: number;
  quorum: number;
}) {
  return (
    <p className="mt-1 text-xs text-slate-500">
      {quorate
        ? `Settled over ${count} independent readings.`
        : `${count} of the ${quorum} readings this platform wants before calling anything settled — everything below is at that width.`}
    </p>
  );
}

function BusinessUnderstandingCard({
  business,
  absent,
}: {
  business: DossierBusinessUnderstanding | null;
  absent: string | null;
}) {
  if (business === null) {
    return <NotRead title="How it creates value" reason={absent} />;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
      <p className="text-sm font-semibold text-slate-800">
        How it creates value
      </p>

      <Quorum
        quorate={business.quorate}
        count={business.observationCount}
        quorum={business.quorum}
      />

      <p className="mt-3 text-sm leading-6 text-slate-700">{business.engine}</p>

      {business.archetype ? (
        <p className="mt-2 flex items-center gap-2 text-sm text-slate-600">
          <span>
            The rules read this as{" "}
            <span className="font-semibold text-slate-800">
              {business.archetype}
            </span>
          </span>
          <Width agreement={business.narrowest} />
        </p>
      ) : business.undecidedBecause ? (
        <p className="mt-2 text-sm leading-6 text-slate-500">
          {business.undecidedBecause}
        </p>
      ) : null}

      {business.segments.length > 0 ? (
        <ul className="mt-4 space-y-1.5">
          {business.segments.map((segment) => (
            <li key={segment.name} className="text-sm">
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-slate-700">{segment.name}</span>
                <span className="shrink-0 tabular-nums text-slate-500">
                  {segment.share === null
                    ? "unmeasured"
                    : `${(segment.share * 100).toFixed(1)}%`}
                </span>
              </div>
              {segment.depends ? (
                /* The filer's own claim, worded by the backend with its
                   degree intact; the verbatim span rides in the tooltip
                   so a reader can check the platform against the filer.
                   Rendered only where stated — a segment without one
                   shows nothing, never "independent". */
                <p
                  className="mt-0.5 text-xs leading-5 text-slate-500"
                  title={segment.dependsQuoted ?? undefined}
                >
                  {segment.depends}
                  {segment.dependsSupport ? (
                    <span className="text-slate-400">
                      {" "}
                      ({segment.dependsSupport})
                    </span>
                  ) : null}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      ) : business.segmentsBecause ? (
        <p className="mt-4 text-sm leading-6 text-slate-500">
          {business.segmentsBecause}
        </p>
      ) : null}

      {business.mechanisms.length > 0 ? (
        <div className="mt-4 border-t border-slate-100 pt-3">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            How it earns
          </p>

          <ul className="mt-2 space-y-1.5">
            {business.mechanisms.map((mechanism) => (
              <li
                key={mechanism.model}
                className="flex items-baseline justify-between gap-3 text-sm"
              >
                <span className="text-slate-700">{mechanism.model}</span>

                <span className="flex shrink-0 items-baseline gap-2">
                  {mechanism.coverage === null ? (
                    <span className="text-slate-400">coverage unmeasured</span>
                  ) : (
                    <span
                      className="tabular-nums text-slate-500"
                      title="The share of measured revenue whose segments earn this way. Not a split of revenue between ways of earning — no filing states that."
                    >
                      {(mechanism.coverage * 100).toFixed(0)}% covered
                    </span>
                  )}
                  <Width agreement={mechanism.support} />
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {business.notEstablished.length > 0 ? (
        <details className="mt-4 border-t border-slate-100 pt-3">
          <summary className="cursor-pointer text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Not established ({business.notEstablished.length})
          </summary>

          <ul className="mt-2 space-y-2 text-sm leading-6 text-slate-500">
            {business.notEstablished.map((item) => (
              <li key={`${item.segment}-${item.dimension}`}>
                <span className="font-medium text-slate-700">
                  {item.segment}
                </span>{" "}
                — {item.because}
              </li>
            ))}
          </ul>
        </details>
      ) : null}

      <p className="mt-4 text-xs leading-5 text-slate-400">{business.source}</p>
    </div>
  );
}

/** How a measure's number should be read, worded by the backend's unit. */
function measureValue(measure: DossierMeasure): string {
  if (measure.value === null) {
    return "not established";
  }

  if (measure.unit === "fraction") {
    return `${(measure.value * 100).toFixed(1)}%`;
  }

  if (measure.unit === "multiple") {
    return `${measure.value.toFixed(2)}×`;
  }

  return measure.value.toLocaleString();
}

function FinancialUnderstandingCard({
  financial,
  absent,
}: {
  financial: DossierFinancialUnderstanding | null;
  absent: string | null;
}) {
  if (financial === null) {
    return <NotRead title="What its statements measure" reason={absent} />;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
      <p className="text-sm font-semibold text-slate-800">
        What its statements measure
      </p>

      <Quorum
        quorate={financial.quorate}
        count={financial.observationCount}
        quorum={financial.quorum}
      />

      {financial.language ? (
        <p
          className="mt-3 text-sm leading-6 text-slate-700"
          title="Which financial language the income statement is written in, from the lines the filer printed. It does not select how this security is read — that is still derived from the business playbook."
        >
          Its income statement speaks a{" "}
          <span className="font-semibold text-slate-800">
            {financial.language}
          </span>{" "}
          language.
        </p>
      ) : null}

      <dl className="mt-4 space-y-2">
        {financial.measures.map((measure) => (
          <div key={measure.measure}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <dt className="text-slate-700">{measure.label}</dt>

              <dd className="flex shrink-0 items-baseline gap-2">
                <span
                  className={
                    measure.value === null
                      ? "text-slate-400"
                      : "font-semibold tabular-nums text-slate-800"
                  }
                >
                  {measureValue(measure)}
                </span>
                <Width agreement={measure.support} />
              </dd>
            </div>

            <p className="mt-0.5 text-xs leading-5 text-slate-400">
              {measure.value === null ? measure.absentBecause : measure.stated}
            </p>
          </div>
        ))}
      </dl>

      <p className="mt-4 text-xs leading-5 text-slate-400">
        {financial.source}
      </p>
    </div>
  );
}

/**
 * The case in words — communication, never judgment.
 *
 * Every paragraph names the findings it rests on, and each citation
 * resolves to a canonical statement shown on hover. The recommendation
 * in this prose is a backend-validated echo of the decision above it;
 * a draft that tried to change it never reached this page.
 */

/** Level 1: the decision itself, before any data. */
function DecisionHeader({ dossier }: { dossier: DossierViewModel }) {
  return (
    <section aria-labelledby="decision-heading">
      {/* What kind of case this is — "Equity dossier", "Crypto dossier" —
          declared by the backend's dossier definition. The first thing
          that says one security is ownership in a business and another
          is a crypto asset, before any section does. */}
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        {dossier.definition.title}
      </p>

      <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
        <h1
          id="decision-heading"
          className="text-4xl font-semibold tracking-[-0.045em] text-slate-950 sm:text-5xl"
        >
          {dossier.symbol}
        </h1>

        <div className="text-right">
          <p className="text-2xl font-semibold tracking-tight text-slate-950">
            {dossier.decisionState}
          </p>

          <p className="mt-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            The investor decides
          </p>
        </div>
      </div>

      <dl className="mt-8 grid gap-px overflow-hidden rounded-[24px] border border-slate-200 bg-slate-200 sm:grid-cols-3">
        <div className="bg-white p-5">
          <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Conviction
          </dt>

          {/* Withheld where the decision cites no supporting reason. Shown
              as the absence it is: a blank beside "/ 100" would read as a
              number that failed to load, and a 0 as the lowest conviction
              the scale can express. Neither is what happened. */}
          <dd
            className={`mt-2 text-xl font-semibold ${
              dossier.conviction === null ? "text-slate-400" : "text-slate-950"
            }`}
          >
            {dossier.conviction === null
              ? "Not stated"
              : `${dossier.conviction} / 100`}
          </dd>

          <p className="mt-1 text-xs text-slate-500">
            {dossier.convictionLabel === null
              ? "The Artificial CIO put no conviction on this case: it cites no supporting reason."
              : `${dossier.convictionLabel} — the Artificial CIO's own view`}
          </p>
        </div>

        <div className="bg-white p-5">
          <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Committee agreement
          </dt>

          {/* Distinct from conviction: how far the committees that spoke
              agreed. Null means none could form a view — not disagreement. */}
          <dd
            className={`mt-2 text-xl font-semibold ${
              dossier.committeeAgreement === null
                ? "text-slate-400"
                : "text-slate-950"
            }`}
          >
            {dossier.committeeAgreement === null
              ? "Not measured"
              : `${Math.round(dossier.committeeAgreement * 100)}%`}
          </dd>

          <p className="mt-1 text-xs text-slate-500">
            {dossier.committeeAgreement === null
              ? "No committee could form a view"
              : "Across the committees that spoke"}
          </p>
        </div>

        <div className="bg-white p-5">
          <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Evidence read
          </dt>

          {/* The domain words the age itself, source and degraded state
              included — rendered verbatim, never re-derived. */}
          <dd
            className={`mt-2 text-sm font-semibold leading-6 ${
              dossier.evidenceAsOf === null
                ? "text-slate-400"
                : "text-slate-950"
            }`}
          >
            {dossier.evidenceAsOf === null
              ? "Not dated"
              : dossier.evidenceAsOf.age}
          </dd>

          <p className="mt-1 text-xs text-slate-500">
            {dossier.evidenceAsOf === null
              ? "No security evidence carries a date"
              : "When the security's own evidence was read"}
          </p>
        </div>
      </dl>
    </section>
  );
}

function FundCost({ cost }: { cost: DossierFundCost }) {
  /* An evidenced fact about the wrapper, rendered in the backend's own
     words. Deliberately plain: no band, no colour, no verdict — a cost
     is a figure with a date, and judging it is not this card's job. */
  return (
    <section className="rounded-[24px] border border-slate-200 bg-white p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
        Cost of ownership
      </p>

      <p className="mt-2 text-sm leading-6 text-slate-700">{cost.stated}</p>

      {cost.read ? (
        <p className="mt-2 text-xs text-slate-400">{cost.read.age}</p>
      ) : null}
    </section>
  );
}

function UnevidencedNotice() {
  return (
    <section className="rounded-[24px] border border-amber-200 bg-amber-50 p-6">
      <div className="flex items-start gap-3">
        <CircleAlert
          aria-hidden="true"
          className="mt-0.5 size-5 text-amber-600"
        />

        <div>
          <h2 className="font-semibold text-amber-950">
            No security-level analysis exists for this symbol
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-amber-900">
            The platform gathered nothing about this security itself, which is a
            different situation from a security that was analysed and had gaps.
            Nothing below describes the security until evidence exists.
          </p>
        </div>
      </div>
    </section>
  );
}

/** Question 1 — what changed: the recorded history, never an invented one. */
/**
 * Every time the Artificial CIO changed its mind about this security.
 *
 * The journal has held this all along and the dossier said only
 * "Stable": Volkswagen moved PREPARE → INVESTIGATE → RECOMMEND in five
 * hours on 9 August, and the recorded scores say why — business quality
 * and valuation could not be measured at the middle reading.
 *
 * Every sentence arrives from the backend, including the rationale the
 * CIO recorded at the time. This component orders and labels; it
 * computes no delta and writes no explanation. A score that stopped
 * being measurable is not shown as a fall, because the domain does not
 * say it was one.
 */
function DecisionCourse({ course }: { course: DossierDecisionCourse }) {
  if (course.absentBecause) {
    return (
      <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-500">
        {course.absentBecause}
      </p>
    );
  }

  if (course.transitions.length === 0) {
    return (
      <p className="mt-5 max-w-3xl text-sm leading-7 text-slate-500">
        {course.stated}
      </p>
    );
  }

  return (
    <div className="mt-6 max-w-3xl">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        Every recorded change
      </p>

      <p className="mt-2 text-sm leading-6 text-slate-700">{course.stated}</p>

      <ol className="mt-4 space-y-4 border-l border-slate-200 pl-5">
        {course.transitions.map((change) => (
          <li key={`${change.at}-${change.fromState}-${change.toState}`}>
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span className="text-sm font-semibold text-slate-950">
                {change.stated}
              </span>

              <span className="text-xs text-slate-500">
                {new Date(change.at).toLocaleString("en-GB", {
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>

            {/* The sentence the CIO recorded when it took the decision,
                never one written now about a decision taken then. */}
            <p className="mt-1 text-sm leading-6 text-slate-600">
              {change.rationale}
            </p>

            {change.unexplained ? (
              <p className="mt-1.5 text-sm leading-6 text-slate-500">
                One of these two decisions was recorded before this platform
                kept its scores, so what moved underneath cannot be said.
              </p>
            ) : change.moved.length > 0 ? (
              <ul className="mt-1.5 space-y-1">
                {change.moved.map((line) => (
                  <li
                    key={line}
                    className="flex gap-2.5 text-sm leading-6 text-slate-700"
                  >
                    <span
                      aria-hidden="true"
                      className="mt-2.5 size-1 shrink-0 rounded-full bg-slate-400"
                    />

                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-1.5 text-sm leading-6 text-slate-500">
                No individual score differed between the two decisions.
              </p>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

function WhatChanged({ dossier }: { dossier: DossierViewModel }) {
  return (
    <section aria-labelledby="changed-heading">
      <SectionHeading id="changed-heading">What changed</SectionHeading>

      {dossier.trend ? (
        <p className="mt-4 max-w-3xl text-lg font-medium leading-7 text-slate-900">
          {dossier.trend.stated}
        </p>
      ) : (
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-500">
          This is the first decision the Artificial CIO has recorded for this
          symbol. No earlier history is claimed, and a first review is not a
          stable one.
        </p>
      )}

      {/* Why the conviction moved. Each line is a score that measurably
          differed between the two recorded decisions; an earlier decision
          predating the scores says so rather than showing nothing. */}
      {dossier.convictionChange ? (
        <div className="mt-5 max-w-3xl">
          <p
            className={`text-sm font-semibold ${
              dossier.convictionChange.delta > 0
                ? "text-emerald-700"
                : "text-amber-700"
            }`}
          >
            {dossier.convictionChange.delta > 0 ? "↑" : "↓"}{" "}
            {dossier.convictionChange.stated}, from{" "}
            {dossier.convictionChange.previous}
          </p>

          {dossier.convictionChange.unexplained ? (
            <p className="mt-2 text-sm leading-6 text-slate-500">
              The earlier decision was recorded before this platform kept its
              scores, so what moved underneath cannot be said.
            </p>
          ) : dossier.convictionChange.because.length > 0 ? (
            <ul className="mt-2 space-y-1.5">
              {dossier.convictionChange.because.map((line) => (
                <li
                  key={line}
                  className="flex gap-2.5 text-sm leading-6 text-slate-700"
                >
                  <span
                    aria-hidden="true"
                    className="mt-2.5 size-1 shrink-0 rounded-full bg-slate-400"
                  />

                  <span>{line}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm leading-6 text-slate-500">
              No individual score moved; the conviction reflects the case as a
              whole.
            </p>
          )}
        </div>
      ) : null}

      {dossier.decisionCourse ? (
        <DecisionCourse course={dossier.decisionCourse} />
      ) : null}

      {/* What to consider doing about it — a consideration, never an
          instruction. The investor decides. */}
      {dossier.action ? (
        <div className="mt-5 max-w-3xl rounded-2xl border border-slate-200 bg-white p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            What to consider
          </p>

          <p className="mt-2 text-base font-semibold text-slate-950">
            {dossier.action.statement}
          </p>

          <p className="mt-1.5 text-sm leading-6 text-slate-600">
            {dossier.action.because}
          </p>

          {dossier.action.checkpoint ? (
            <p className="mt-2 text-sm text-slate-500">
              Next: {dossier.action.checkpoint}
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

/** Questions 2 and 4 — why it matters, and what the CIO recommends. */
/**
 * The conclusion, in the three parts an investor needs to argue with it.
 *
 * This replaces a single sentence — "The investment case satisfies
 * quality, evidence, valuation, risk, and portfolio gates" — which was
 * true, identical under every recommendation, and named nothing about
 * the company. That sentence is still shown, once, as what it actually
 * is: the gate the case cleared.
 *
 * Every string here is composed by the backend from canonical objects.
 * This component groups and labels; it selects no fact, writes no
 * sentence and infers no conclusion.
 */
function Synthesis({
  synthesis,
  gate,
}: {
  synthesis: DossierSynthesis;
  gate: string;
}) {
  return (
    <div className="mt-4 overflow-hidden rounded-[24px] border border-slate-200">
      <SynthesisPart
        title="Because"
        facts={synthesis.because}
        absent={synthesis.becauseAbsent}
      />

      <SynthesisPart
        title="Despite"
        facts={synthesis.despite}
        absent={synthesis.despiteAbsent}
        emphasis
      />

      <div className="border-t border-slate-200 bg-white px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
          Review if
        </p>

        {synthesis.reviewIf.length > 0 ? (
          <ul className="mt-3 space-y-3">
            {synthesis.reviewIf.map((condition) => (
              <li key={condition.condition} className="text-sm leading-6">
                <span className="flex items-start gap-2">
                  <OriginMark origin={condition.origin} />
                  <span className="text-slate-800">{condition.condition}</span>
                </span>

                {condition.wouldChange ? (
                  <span className="mt-1 block pl-[3.75rem] text-xs leading-5 text-slate-500">
                    {condition.wouldChange}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm leading-6 text-slate-500">
            {synthesis.reviewIfAbsent}
          </p>
        )}
      </div>

      {/* What is not yet known — its own part, deliberately after the
          two cases and before the decision. A fact against the security
          is a reason to hesitate; something unmeasured is a reason the
          platform cannot yet say, and folding the second into the first
          is how not knowing turns into bearishness. */}
      <div className="border-t border-slate-200 bg-white px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
          Uncertainty
        </p>

        {synthesis.uncertainty.length > 0 ? (
          <ul className="mt-3 space-y-3">
            {synthesis.uncertainty.map((item) => (
              <li key={item.about} className="text-sm leading-6">
                <span className="text-slate-800">{item.about}</span>

                <span className="mt-1 block text-xs leading-5 text-slate-500">
                  {item.committee}
                  {" — "}
                  {item.resolvable
                    ? "a measurement would settle it"
                    : "not a question this platform can answer"}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm leading-6 text-slate-500">
            {synthesis.uncertaintyAbsent}
          </p>
        )}
      </div>

      {/* Why this conclusion and not the other. The part a scoring
          engine cannot write: a conviction figure is the same number
          whether a committee objected or none did. */}
      {synthesis.deliberation ? (
        <div className="border-t border-slate-200 bg-white px-6 py-5">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Decision
          </p>

          <p className="mt-3 text-sm leading-6 text-slate-800">
            {synthesis.deliberation.prevailed}
          </p>

          <p className="mt-2 text-sm leading-6 text-slate-600">
            {synthesis.deliberation.agreement}
          </p>

          {/* The position that did not carry, preserved. */}
          {synthesis.deliberation.over ? (
            <p className="mt-2 border-l-2 border-slate-300 pl-3 text-sm leading-6 text-slate-600">
              {synthesis.deliberation.over}
            </p>
          ) : null}

          <p className="mt-2 text-xs leading-5 text-slate-500">
            {synthesis.deliberation.because}
          </p>
        </div>
      ) : null}

      {synthesis.established.length > 0 ? (
        <details className="border-t border-slate-200 bg-slate-50 px-6 py-5">
          <summary className="cursor-pointer text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            What its own filing establishes ({synthesis.established.length})
          </summary>

          <p className="mt-2 text-xs leading-5 text-slate-500">
            Read from the company&rsquo;s published accounts. None of it reached
            the decision above.
          </p>

          <ul className="mt-3 space-y-2">
            {synthesis.established.map((fact) => (
              <li
                key={fact.statement}
                className="flex items-start gap-2 text-sm leading-6 text-slate-700"
              >
                <OriginMark origin={fact.origin} />
                <span>{fact.statement}</span>
              </li>
            ))}
          </ul>
        </details>
      ) : null}

      <p className="border-t border-slate-200 bg-slate-50 px-6 py-3 text-xs leading-5 text-slate-500">
        Gate cleared: {gate}
      </p>
    </div>
  );
}

/** One part of the conclusion, or the backend's reason it is empty. */
function SynthesisPart({
  title,
  facts,
  absent,
  emphasis,
}: {
  title: string;
  facts: readonly DossierSynthesisFact[];
  absent: string | null;
  emphasis?: boolean;
}) {
  return (
    <div
      className={`px-6 py-5 ${emphasis ? "border-t border-slate-200 bg-amber-50/40" : "bg-white"}`}
    >
      <p
        className={`text-xs font-semibold uppercase tracking-[0.15em] ${
          emphasis ? "text-amber-800" : "text-slate-500"
        }`}
      >
        {title}
      </p>

      {facts.length > 0 ? (
        <ul className="mt-3 space-y-2">
          {facts.map((fact) => (
            <li
              key={fact.statement}
              className="flex items-start gap-2 text-sm leading-6 text-slate-800"
            >
              <OriginMark origin={fact.origin} />
              <span>{fact.statement}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm leading-6 text-slate-500">{absent}</p>
      )}
    </div>
  );
}

/**
 * Where a fact came from, and therefore how far it goes.
 *
 * A figure read out of an audited filing and an analyst's reading of
 * market data are both true and are not the same kind of claim. Printed
 * side by side without this, the weaker borrows the stronger's
 * authority — which is the whole reason the backend attaches an origin.
 */
function OriginMark({ origin }: { origin: string }) {
  const established = origin === "established";

  return (
    <span
      className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
        established ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-500"
      }`}
      title={
        established
          ? "Read from the company's own filing and checked against the cell it sits in."
          : "This platform's analysts, reading market and provider data."
      }
    >
      {established ? "filed" : "assessed"}
    </span>
  );
}

function Recommendation({ dossier }: { dossier: DossierViewModel }) {
  return (
    <section aria-labelledby="recommendation-heading">
      <SectionHeading id="recommendation-heading">
        The recommendation, and why
      </SectionHeading>

      {dossier.synthesis ? (
        <Synthesis synthesis={dossier.synthesis} gate={dossier.rationale} />
      ) : (
        <div className="mt-4 rounded-[24px] border border-slate-200 bg-slate-50 p-6">
          <p className="text-sm leading-7 text-slate-800">{dossier.summary}</p>

          {/* The thesis summary is built from the decision rationale, so
              the two are often the identical sentence. Saying it twice
              reads as a bug, not as emphasis — the rationale is shown
              only where it adds words the summary does not have. */}
          {dossier.rationale !== dossier.summary ? (
            <p className="mt-4 border-t border-slate-200 pt-4 text-sm leading-7 text-slate-600">
              {dossier.rationale}
            </p>
          ) : null}
        </div>
      )}

      <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Expected holding period
          </dt>
          <dd className="mt-2 text-slate-800">
            {dossier.expectedHoldingPeriod}
          </dd>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Next trigger
          </dt>
          <dd
            className={`mt-2 ${
              dossier.nextTrigger === null ? "text-slate-400" : "text-slate-800"
            }`}
          >
            {dossier.nextTrigger ?? "None recorded"}
          </dd>
        </div>
      </dl>

      {dossier.catalysts.length > 0 ? (
        <StatementList
          className="mt-4"
          title="Catalysts"
          items={dossier.catalysts}
        />
      ) : null}

      {dossier.invalidationConditions.length > 0 ? (
        <StatementList
          className="mt-4"
          title="What would invalidate this thesis"
          items={dossier.invalidationConditions}
        />
      ) : null}
    </section>
  );
}

/** Question 3 — why it matters for this investor: account and market facts,
 *  kept strictly apart from facts about the security. */
function InvestorContext({ dossier }: { dossier: DossierViewModel }) {
  return (
    <section aria-labelledby="context-heading">
      <SectionHeading id="context-heading">
        Your portfolio and the market
      </SectionHeading>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
        Facts about your account and current conditions — not about{" "}
        {dossier.symbol} itself. The two are never mixed.
      </p>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <ContextCard
          icon={Scale}
          title="Working in your favour"
          items={dossier.contextStrengths}
          emptyText="Nothing recorded."
        />

        <ContextCard
          icon={ShieldAlert}
          title="Working against you"
          items={dossier.contextRisks}
          emptyText="Nothing recorded."
        />
      </div>

      <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-5 text-sm">
        <span className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
          Portfolio fit
        </span>

        <p
          className={`mt-2 ${
            dossier.scores.portfolioFit.value === null
              ? "text-slate-400"
              : "text-slate-800"
          }`}
        >
          {dossier.scores.portfolioFit.value === null
            ? "Not measured — your policy states no limit this could be measured against"
            : `${dossier.scores.portfolioFit.value} / 100 under your investment policy`}
        </p>
      </div>
    </section>
  );
}

/** Question 5 — why trust this: evidence, scores, committees, provenance. */
function WhyTrustThis({ dossier }: { dossier: DossierViewModel }) {
  return (
    <section aria-labelledby="trust-heading">
      <SectionHeading id="trust-heading">
        Why you can examine this
      </SectionHeading>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
        Every layer of the reasoning is retained and shown below, deepest last.
        An absent measurement is reported as absent.
      </p>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <ContextCard
          icon={Scale}
          title={`For ${dossier.symbol}`}
          items={dossier.strengths}
          emptyText="No finding argued for this security."
        />

        <ContextCard
          icon={ShieldAlert}
          title={`Against ${dossier.symbol}`}
          items={dossier.risks}
          emptyText="No finding argued against this security."
        />
      </div>

      {dossier.missingEvidence.length > 0 ? (
        <StatementList
          className="mt-4"
          title="Missing or unmeasured"
          items={dossier.missingEvidence}
          muted
        />
      ) : null}

      <Scores dossier={dossier} />

      <Committees committees={dossier.committees} />

      {dossier.evidenceWeighed.length > 0 ? (
        <details className="mt-4 rounded-2xl border border-slate-200 bg-white px-5 py-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-800">
            Every finding weighed ({dossier.evidenceWeighed.length})
          </summary>

          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
            {dossier.evidenceWeighed.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}

/**
 * The five scores, each opening onto the backend's account of itself.
 *
 * A score is the most measurement-looking thing on the page and the least
 * measured: most are a band this platform chose, applied to a reading it
 * took. Every row therefore expands to the sentence that produced the
 * number and the findings underneath it — both written by the pipeline
 * that scored it. Nothing here explains a score; it only discloses the
 * explanation.
 */
/**
 * What separates two scores that landed on the same number.
 *
 * A dot per factor, coloured by the sense the backend recorded, then
 * the two counts it computed: how much of what was read came back
 * favourable, and how much of the question set could be read at all.
 * They answer different questions — the first about the business, the
 * second about this platform — and a page showing only the score shows
 * neither.
 *
 * Every value is a field. Nothing here parses a sentence, compares a
 * threshold or decides what a verdict means.
 */
function VerdictStrip({ derivation }: { derivation: DossierDerivation }) {
  const tone: Record<string, string> = {
    favourable: "bg-emerald-500",
    adverse: "bg-rose-400",
    neutral: "bg-slate-300",
  };

  return (
    <span className="flex items-center gap-2 text-xs text-slate-500">
      <span aria-hidden className="flex items-center gap-1">
        {derivation.contributions.map((item, index) => (
          <span
            key={`${item.statement}-${index}`}
            className={`h-1.5 w-1.5 rounded-full ${
              tone[item.sense] ?? "bg-slate-300"
            }`}
          />
        ))}
      </span>

      <span className="tabular-nums">
        {derivation.earned} of {derivation.available} favourable
      </span>

      {derivation.coverage ? (
        <>
          <span aria-hidden className="text-slate-300">
            ·
          </span>

          {/* Every readable factor scored and the band still fell short.
              Without this, "2 of 2 favourable" beside 62 reads as a
              broken score rather than as thin coverage. The boolean and
              the sentence are both the backend's; this only shows them. */}
          <span
            className={`tabular-nums ${
              derivation.cappedByUnreadableFactors
                ? "font-medium text-amber-700"
                : ""
            }`}
            title={
              derivation.cappedByUnreadableFactors
                ? derivation.stated
                : undefined
            }
          >
            {derivation.coverage}
            {derivation.cappedByUnreadableFactors ? " — band limited" : ""}
          </span>
        </>
      ) : null}
    </span>
  );
}

/**
 * Why the number is the number: the factors counted, and what each was worth.
 *
 * Every figure here is the backend's. This lays them out and adds no
 * arithmetic of its own — a total computed on this side could disagree
 * with the score it sits under, which is the one thing a breakdown must
 * never do.
 *
 * There are no negative contributions, because the platform has none: a
 * factor the company fails earns no point rather than subtracting one.
 * That is said in words, since a column of zeroes otherwise reads as
 * nothing having counted against.
 */
function ScoreBreakdown({ derivation }: { derivation: DossierDerivation }) {
  const hasZero = derivation.contributions.some((item) => item.points === 0);

  return (
    <div className="mt-3 max-w-2xl">
      <ul className="text-sm leading-6">
        {derivation.contributions.map((item) => (
          <li
            key={item.statement}
            className="flex items-baseline justify-between gap-4 border-b border-slate-200/70 py-1.5 last:border-0"
          >
            <span
              className={item.points > 0 ? "text-slate-700" : "text-slate-500"}
            >
              {item.statement}

              {/* The analyst's own word, shown rather than folded into
                  the sentence above it. */}
              {item.verdict ? (
                <span className="ml-2 text-xs uppercase tracking-wide text-slate-400">
                  {item.verdict}
                </span>
              ) : null}
            </span>

            {/* A zero is not one thing: a factor that does not apply and
                one the company failed are different, and the sense is
                what tells them apart. */}
            <span className="flex shrink-0 items-baseline gap-2 tabular-nums">
              {item.points === 0 ? (
                <span className="text-xs text-slate-400">
                  {item.sense === "adverse" ? "not earned" : "n/a"}
                </span>
              ) : null}

              <span
                className={
                  item.points > 0
                    ? "font-semibold text-slate-950"
                    : "font-medium text-slate-400"
                }
              >
                {item.points > 0 ? `+${item.points}` : "0"}
              </span>
            </span>
          </li>
        ))}
      </ul>

      <p className="mt-2 text-sm font-medium text-slate-800">
        {derivation.stated}
      </p>

      {/* The score was held down by what could be read, not by the
          company. Worth saying outright: the investor would otherwise
          read a middling band as a verdict on the business. */}
      {derivation.cappedByUnreadableFactors ? (
        <p className="mt-1.5 text-xs leading-5 text-amber-700">
          This is a limit of what the platform could read, not a finding about
          the company.
        </p>
      ) : null}

      {hasZero ? (
        <p className="mt-1.5 text-xs leading-5 text-slate-500">
          Nothing subtracts: a factor the company does not meet earns no point
          rather than losing one.
        </p>
      ) : null}

      <p className="mt-1.5 text-xs leading-5 text-slate-400">
        {derivation.scale
          .map(([band, value]) => `${band} ${value}`)
          .join(" · ")}
      </p>
    </div>
  );
}

function Scores({ dossier }: { dossier: DossierViewModel }) {
  // Each score arrives carrying its own name from the backend's dossier
  // definition — "Business quality" on an equity, "Asset quality" on a
  // token. Naming them here made every dossier a company dossier.
  const rows: readonly { label: string; score: DossierScore }[] = [
    dossier.scores.quality,
    dossier.scores.evidence,
    dossier.scores.valuation,
    dossier.scores.safety,
    dossier.scores.portfolioFit,
  ].map((score) => ({ label: score.label, score }));

  return (
    <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
      <div className="border-b border-slate-200 bg-slate-50 px-5 py-3">
        <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
          The scores the decision was made on
        </p>

        {/* Said once, at the top, because it is the property that makes
            the set readable at all: risk is shown as safety so that no
            single dimension runs against the others. */}
        <p className="mt-1 text-xs text-slate-500">
          Every score runs the same way — a higher number is better for the
          case. Open one to see what produced it.
        </p>
      </div>

      <div className="divide-y divide-slate-100 bg-white">
        {rows.map((row) => (
          <details key={row.label} className="group">
            <summary className="flex cursor-pointer items-center justify-between gap-4 px-5 py-3 text-sm hover:bg-slate-50">
              <span className="flex items-center gap-2 text-slate-600">
                {row.label}

                <ChevronDown
                  aria-hidden
                  className="h-4 w-4 text-slate-400 transition-transform group-open:rotate-180"
                />

                <span className="sr-only">Why this score</span>
              </span>

              <span className="ml-auto flex items-center gap-3">
                {/* Two scores can coincide on entirely different
                    evidence — three companies sat at 62 on a
                    favourable-of-answered of 1 of 3, and only the
                    verdicts told them apart. Every value here is a
                    backend field; nothing is parsed or judged. */}
                {row.score.derivation ? (
                  <VerdictStrip derivation={row.score.derivation} />
                ) : null}

                {/* Null is not zero: a score nobody measured says so. */}
                <span
                  className={
                    row.score.value === null
                      ? "font-medium text-slate-400"
                      : "font-semibold text-slate-950"
                  }
                >
                  {row.score.value === null
                    ? "Not measured"
                    : `${row.score.value} / 100`}
                </span>
              </span>
            </summary>

            <div className="border-t border-slate-100 bg-slate-50/60 px-5 py-4">
              {/* Measured, policy-derived and assessed numbers look alike
                  at two significant figures, and the assessment borrows
                  the measurement's authority unless it is labelled. */}
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
                {row.score.kindStated}
              </p>

              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                {row.score.basis}
              </p>

              {/* Where the score counted factors, they are shown with what
                  each was worth — the same findings, with the arithmetic
                  that produced the number. The plain list is the fallback
                  for scores that band one reading, which have no
                  decomposition to show. */}
              {row.score.derivation ? (
                <ScoreBreakdown derivation={row.score.derivation} />
              ) : row.score.evidence.length > 0 ? (
                <ul className="mt-3 space-y-1.5 text-sm leading-6 text-slate-600">
                  {row.score.evidence.map((item) => (
                    <li key={item} className="flex gap-2">
                      <span aria-hidden className="text-slate-300">
                        —
                      </span>

                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}

/**
 * The findings a committee's position stands on, in the order read.
 *
 * Deliberately not numbered or ranked: this platform does not measure
 * how strong a finding is, and a list presented as strongest-first
 * would be an ordering nobody took.
 */
function CommitteeGrounds({
  label,
  statements,
}: {
  label: string;
  statements: readonly string[];
}) {
  if (statements.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 border-t border-slate-100 pt-3">
      <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
        {label}
      </p>

      <ul className="mt-2 space-y-1.5 text-sm leading-6 text-slate-600">
        {statements.map((statement) => (
          <li key={statement}>{statement}</li>
        ))}
      </ul>
    </div>
  );
}

function Committees({
  committees,
}: {
  committees: readonly DossierCommitteeOpinion[];
}) {
  if (committees.length === 0) {
    return (
      <p className="mt-4 text-sm leading-6 text-slate-500">
        No committee reviewed this case.
      </p>
    );
  }

  return (
    <div className="mt-4 space-y-3">
      {committees.map((opinion) => (
        <details
          key={opinion.committee}
          className="rounded-2xl border border-slate-200 bg-white px-5 py-4"
        >
          <summary className="flex cursor-pointer flex-wrap items-center gap-3 text-sm">
            <span className="font-semibold text-slate-950">
              {opinion.committee}
            </span>

            {/* A stance, never an action: only the Artificial CIO says
                what to do. An abstention is labelled as an inability to
                take a position, and never rendered as a negative one. */}
            {opinion.abstained || opinion.stance === null ? (
              <StatusPill status="partial" label="Took no position" />
            ) : (
              <>
                <span className="font-medium uppercase tracking-wide text-slate-600">
                  {opinion.stance}
                </span>

                {/* The backend words this with its own counts. It
                    measures the reading, not the security. */}
                <span className="text-xs text-slate-500">
                  {opinion.confidence}
                </span>
              </>
            )}
          </summary>

          <p className="mt-3 text-sm leading-6 text-slate-600">
            {opinion.abstained
              ? (opinion.abstainedBecause ?? opinion.summary)
              : opinion.summary}
          </p>

          {/* The findings the position stands on. Each one is resolved
              by the backend from the case's own ledger, so nothing here
              is prose a committee composed about itself. */}
          <CommitteeGrounds label="For" statements={opinion.supporting} />
          <CommitteeGrounds label="Against" statements={opinion.opposing} />

          {opinion.uncertainty.length > 0 ? (
            <ul className="mt-3 space-y-1.5 border-t border-slate-100 pt-3 text-sm leading-6 text-slate-600">
              {opinion.uncertainty.map((item) => (
                <li key={item.about}>
                  <span className="text-slate-500">{item.about}</span>

                  {/* Never shown as pending where nothing is coming. */}
                  <span className="ml-2 text-xs text-slate-400">
                    {item.resolvable
                      ? "a measurement would settle it"
                      : "not a question this platform can answer"}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}

          <p className="mt-3 text-xs text-slate-400">
            Decided by rule {opinion.decidedBy}
          </p>
        </details>
      ))}
    </div>
  );
}

function SectionHeading({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  return (
    <h2
      id={id}
      className="text-2xl font-semibold tracking-[-0.03em] text-slate-950"
    >
      {children}
    </h2>
  );
}

function ContextCard({
  icon: Icon,
  title,
  items,
  emptyText,
}: {
  icon: typeof Scale;
  title: string;
  items: readonly string[];
  emptyText: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-center gap-2">
        <Icon aria-hidden="true" className="size-4 text-slate-400" />

        <h3 className="text-sm font-semibold text-slate-950">{title}</h3>
      </div>

      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-400">{emptyText}</p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function StatementList({
  title,
  items,
  className,
  muted = false,
}: {
  title: string;
  items: readonly string[];
  className?: string;
  muted?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white p-5 ${className ?? ""}`}
    >
      <h3 className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
        {title}
      </h3>

      <ul
        className={`mt-3 space-y-2 text-sm leading-6 ${
          muted ? "text-slate-500" : "text-slate-600"
        }`}
      >
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
