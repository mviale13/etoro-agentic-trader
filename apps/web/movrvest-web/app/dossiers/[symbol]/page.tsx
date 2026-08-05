import Link from "next/link";
import {
  ArrowLeft,
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
  DossierCommitteeOpinion,
  DossierNarrative,
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

      <WhatChanged dossier={dossier} />
      <Recommendation dossier={dossier} />
      <InvestorContext dossier={dossier} />
      <WhyTrustThis dossier={dossier} />
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

      <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-700">
        {dossier.previousDecisions ??
          "This is the first decision the Artificial CIO has recorded for this symbol. No earlier history is claimed."}
      </p>
    </section>
  );
}

/** Questions 2 and 4 — why it matters, and what the CIO recommends. */
function Recommendation({ dossier }: { dossier: DossierViewModel }) {
  return (
    <section aria-labelledby="recommendation-heading">
      <SectionHeading id="recommendation-heading">
        The recommendation, and why
      </SectionHeading>

      <div className="mt-4 rounded-[24px] border border-slate-200 bg-slate-50 p-6">
        <p className="text-sm leading-7 text-slate-800">{dossier.summary}</p>

        <p className="mt-4 border-t border-slate-200 pt-4 text-sm leading-7 text-slate-600">
          {dossier.rationale}
        </p>
      </div>

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
            dossier.scores.portfolioFit === null
              ? "text-slate-400"
              : "text-slate-800"
          }`}
        >
          {dossier.scores.portfolioFit === null
            ? "Not measured — your policy states no limit this could be measured against"
            : `${dossier.scores.portfolioFit} / 100 under your investment policy`}
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

function Scores({ dossier }: { dossier: DossierViewModel }) {
  const rows: readonly { label: string; value: number | null }[] = [
    { label: "Business quality", value: dossier.scores.quality },
    { label: "Evidence", value: dossier.scores.evidence },
    { label: "Valuation", value: dossier.scores.valuation },
    { label: "Risk", value: dossier.scores.risk },
    { label: "Portfolio fit", value: dossier.scores.portfolioFit },
  ];

  return (
    <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
      <p className="border-b border-slate-200 bg-slate-50 px-5 py-3 text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
        The scores the decision was made on
      </p>

      <dl className="divide-y divide-slate-100 bg-white">
        {rows.map((row) => (
          <div
            key={row.label}
            className="flex items-center justify-between px-5 py-3 text-sm"
          >
            <dt className="text-slate-600">{row.label}</dt>

            {/* Null is not zero: a score nobody measured says so. */}
            <dd
              className={
                row.value === null
                  ? "font-medium text-slate-400"
                  : "font-semibold text-slate-950"
              }
            >
              {row.value === null ? "Not measured" : `${row.value} / 100`}
            </dd>
          </div>
        ))}
      </dl>
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
