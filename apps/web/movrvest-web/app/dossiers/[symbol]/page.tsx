import Link from "next/link";
import {
  ArrowLeft,
  ChevronDown,
  CircleAlert,
  PenLine,
  Scale,
  ShieldAlert,
} from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";
import { StatusPill } from "@/components/ui/StatusPill";
import { getDossier } from "@/lib/api/dossier";
import type {
  DossierAgreement,
  DossierBusinessUnderstanding,
  DossierCommitteeOpinion,
  DossierFinancialUnderstanding,
  DossierMeasure,
  DossierPlaybook,
  DossierNarrative,
  DossierScore,
  DossierSynthesis,
  DossierSynthesisFact,
  DossierUnderstanding,
  DossierViewModel,
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
function Playbook({ playbook }: { playbook: DossierPlaybook }) {
  return (
    <section
      aria-labelledby="playbook-heading"
      className="rounded-[28px] border border-slate-200 bg-white p-8"
    >
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        Company type
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

                  {item.reason ? (
                    <span className="block text-slate-500">
                      Not applicable — {item.reason}
                    </span>
                  ) : null}
                </span>
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
      <DecisionHeader dossier={dossier} />

      {dossier.securityEvidenced ? null : <UnevidencedNotice />}

      {dossier.narrative ? (
        <Narrative narrative={dossier.narrative} />
      ) : dossier.narrativeAbsent ? (
        <NarrativeAbsence reason={dossier.narrativeAbsent} />
      ) : null}

      {dossier.playbook ? <Playbook playbook={dossier.playbook} /> : null}

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
            <li
              key={segment.name}
              className="flex items-baseline justify-between gap-3 text-sm"
            >
              <span className="text-slate-700">{segment.name}</span>
              <span className="shrink-0 tabular-nums text-slate-500">
                {segment.share === null
                  ? "unmeasured"
                  : `${(segment.share * 100).toFixed(1)}%`}
              </span>
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

      <p className="mt-4 text-xs leading-5 text-slate-400">{financial.source}</p>
    </div>
  );
}

const SECTION_TITLES: Record<string, string> = {
  executive_summary: "Executive summary",
  why_now: "Why now",
  trade_off: "The trade-off",
  committee_summary: "What the committees said",
  thesis_invalidators: "What would invalidate this thesis",
};

/**
 * The case in words — communication, never judgment.
 *
 * Every paragraph names the findings it rests on, and each citation
 * resolves to a canonical statement shown on hover. The recommendation
 * in this prose is a backend-validated echo of the decision above it;
 * a draft that tried to change it never reached this page.
 */
function Narrative({ narrative }: { narrative: DossierNarrative }) {
  const findingById = new Map(
    narrative.findings.map((finding) => [finding.id, finding]),
  );

  return (
    <section
      aria-labelledby="narrative-heading"
      className="rounded-[28px] border border-slate-200 bg-white p-8"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
            <PenLine aria-hidden="true" className="h-5 w-5" />
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Executive narrative
            </p>

            <h2
              id="narrative-heading"
              className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-slate-950"
            >
              {narrative.headline}
            </h2>
          </div>
        </div>

        <StatusPill
          status="partial"
          label="AI-written, grounded"
          explanation="Written by the Executive Writer from the Artificial CIO's own findings and nothing else. Every paragraph cites its findings; the recommendation is a validated echo of the decision. The writer never decides."
        />
      </div>

      <div className="mt-6 space-y-6">
        {narrative.sections.map((section) => (
          <div key={section.section}>
            <h3 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">
              {SECTION_TITLES[section.section] ?? section.section}
            </h3>

            <p className="mt-2 leading-7 text-slate-700">{section.text}</p>

            <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
              <span>Grounded in</span>

              {section.findingIds.map((id) => (
                <span
                  className="cursor-help rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-500"
                  key={id}
                  title={
                    findingById.get(id)
                      ? `${findingById.get(id)!.statement} — ${findingById.get(id)!.source}`
                      : id
                  }
                >
                  {id}
                </span>
              ))}
            </p>
          </div>
        ))}
      </div>

      <p className="mt-6 border-t border-slate-100 pt-4 text-xs text-slate-500">
        {narrative.written}. Language only: the structured case below is
        canonical, and the Artificial CIO owns every judgment in it.
      </p>
    </section>
  );
}

/**
 * The backend-worded reason there is no narrative.
 *
 * The Executive Writer words every failure path — flag off, missing
 * credentials, a declined request, a discarded draft — precisely so a
 * surface can state it. Presenting that sentence is this page's whole
 * job here; it adds nothing and hides nothing.
 */
function NarrativeAbsence({ reason }: { reason: string }) {
  return (
    <p className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-4 text-sm text-slate-500">
      {reason}
    </p>
  );
}

/** Level 1: the decision itself, before any data. */
function DecisionHeader({ dossier }: { dossier: DossierViewModel }) {
  return (
    <section aria-labelledby="decision-heading">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        Investment dossier
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

          <dd className="mt-2 text-xl font-semibold text-slate-950">
            {dossier.conviction} / 100
          </dd>

          <p className="mt-1 text-xs text-slate-500">
            {dossier.convictionLabel} — the Artificial CIO&apos;s own view
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
            The platform gathered nothing about this security itself, which is
            a different situation from a security that was analysed and had
            gaps. Nothing below describes the security until evidence exists.
          </p>
        </div>
      </div>
    </section>
  );
}

/** Question 1 — what changed: the recorded history, never an invented one. */
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

      {synthesis.established.length > 0 ? (
        <details className="border-t border-slate-200 bg-slate-50 px-6 py-5">
          <summary className="cursor-pointer text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            What its own filing establishes ({synthesis.established.length})
          </summary>

          <p className="mt-2 text-xs leading-5 text-slate-500">
            Read from the company&rsquo;s published accounts. None of it
            reached the decision above.
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
        established
          ? "bg-slate-800 text-white"
          : "bg-slate-100 text-slate-500"
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
      <SectionHeading id="trust-heading">Why you can examine this</SectionHeading>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
        Every layer of the reasoning is retained and shown below, deepest
        last. An absent measurement is reported as absent.
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
function Scores({ dossier }: { dossier: DossierViewModel }) {
  const rows: readonly { label: string; score: DossierScore }[] = [
    { label: "Business quality", score: dossier.scores.quality },
    { label: "Evidence strength", score: dossier.scores.evidence },
    { label: "Valuation attractiveness", score: dossier.scores.valuation },
    { label: "Safety", score: dossier.scores.safety },
    { label: "Portfolio fit", score: dossier.scores.portfolioFit },
  ];

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

              {row.score.evidence.length > 0 ? (
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

            {/* An abstention is not opposition: it is labelled as an
                inability to form a view, never rendered as a "sell". */}
            {opinion.abstained ? (
              <StatusPill status="partial" label="Could not form a view" />
            ) : (
              <>
                <span className="font-medium uppercase tracking-wide text-slate-600">
                  {opinion.recommendation.replace(/_/g, " ")}
                </span>

                <span className="text-xs text-slate-500">
                  {opinion.confidence === null
                    ? null
                    : `${Math.round(opinion.confidence * 100)}% confident`}
                </span>
              </>
            )}
          </summary>

          <p className="mt-3 text-sm leading-6 text-slate-600">
            {opinion.summary}
          </p>

          {opinion.evidence.length > 0 ? (
            <ul className="mt-3 space-y-1.5 border-t border-slate-100 pt-3 text-sm leading-6 text-slate-600">
              {opinion.evidence.map((item) => (
                <li key={`${item.source}-${item.statement}`}>
                  {item.statement}
                  <span className="ml-2 text-xs text-slate-400">
                    {item.source}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
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
