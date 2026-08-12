import Link from "next/link";
import { ArrowLeft, CircleAlert } from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";
import {
  getCryptoCorpus,
  getCryptoDossier,
  type CommitteeCellView,
  type CorpusAsset,
  type CryptoDossier,
  type CryptoIdentity,
  type CryptoQuestionView,
  type IntelligenceView,
  type InvestorStatementView,
  type IssuanceView,
  type JournalView,
  type MarketView,
  type QualityView,
  type SupplyView,
} from "@/lib/api/crypto-dossier";

export const dynamic = "force-dynamic";

type PageProps = { params: Promise<{ symbol: string }> };

/**
 * Everything this platform can say about one digital asset.
 *
 * **A token is not a company with different labels.** The equity dossier
 * leads with a conviction, a score and a committee agreement, because
 * that is what an equity case is. None of those exist here: crypto Asset
 * Quality reads UNKNOWN for every asset by design, the two crypto
 * committees answer different structural questions and are never
 * combined, and there is no recommendation layer. This page is
 * organised around what is actually known, in the order an investor
 * meets it.
 *
 * **It computes nothing.** Every sentence arrives worded from the
 * backend — applicability from the archetype, meaning from the
 * licensing contract, verdicts in each committee's own words. There is
 * no threshold, no band, no ranking and no fallback prose here. Where
 * the backend declines to interpret a measurement, this page renders
 * the declining sentence rather than a friendlier one of its own.
 */
export default async function CryptoDossierPage({ params }: PageProps) {
  const { symbol } = await params;
  const asset = symbol.toUpperCase();

  const [result, corpus] = await Promise.all([
    getCryptoDossier(asset),
    getCryptoCorpus(),
  ]);

  return (
    <DashboardLayout>
      <PageIntegrity
        status={result.source === "backend" ? "live" : "placeholder"}
        endpoint={
          result.source === "backend" ? `/crypto/${asset}/dossier` : undefined
        }
        description={
          result.source === "backend"
            ? "Every section is read from stored evidence and recorded judgments. Opening this page fetches nothing, asks no model and records no judgment. Absent evidence is shown as absent."
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

        <Switcher corpus={corpus} current={asset} />

        {result.dossier ? (
          <Sections dossier={result.dossier} />
        ) : (
          <Unavailable url={result.backendUrl} error={result.error} />
        )}
      </main>
    </DashboardLayout>
  );
}

/** Move between assets without losing the reading position in the head. */
function Switcher({
  corpus,
  current,
}: {
  corpus: readonly CorpusAsset[];
  current: string;
}) {
  if (corpus.length === 0) {
    return null;
  }

  return (
    <nav aria-label="Digital assets" className="mt-6 flex flex-wrap gap-2">
      {corpus.map((asset) => (
        <Link
          key={asset.symbol}
          href={`/crypto/${asset.symbol}`}
          aria-current={asset.symbol === current ? "page" : undefined}
          className={
            asset.symbol === current
              ? "rounded-full bg-slate-950 px-4 py-1.5 text-sm font-semibold text-white"
              : "rounded-full border border-slate-200 px-4 py-1.5 text-sm font-semibold text-slate-600 hover:border-slate-400 hover:text-slate-950"
          }
        >
          {asset.symbol}
          <span className="ml-2 font-normal text-xs opacity-70">
            {asset.name}
          </span>
        </Link>
      ))}
    </nav>
  );
}

function Unavailable({ url, error }: { url: string; error?: string }) {
  return (
    <section className="mt-8 rounded-[28px] border border-amber-200 bg-amber-50 px-8 py-10">
      <h1 className="text-xl font-semibold text-amber-950">
        Nothing is held for this asset
      </h1>
      <p className="mt-3 max-w-2xl text-sm leading-relaxed text-amber-900">
        The backend did not serve a dossier. Nothing is shown in its place,
        because a page of plausible-looking sections is worse than an empty one.
      </p>
      <p className="mt-4 font-mono text-xs text-amber-800">{url}</p>
      {error ? (
        <p className="mt-2 font-mono text-xs text-amber-700">{error}</p>
      ) : null}
    </section>
  );
}

function Sections({ dossier }: { dossier: CryptoDossier }) {
  return (
    <div className="mt-8 space-y-10">
      <Identity symbol={dossier.symbol} identity={dossier.identity} />
      <Assessment assessment={dossier.assessment} />
      <Committees committees={dossier.committees.committees} />
      <Questions identity={dossier.identity} quality={dossier.quality} />
      <Supply supply={dossier.supply} issuance={dossier.issuance} />
      <Market market={dossier.market} />
      <Happening intelligence={dossier.intelligence} />
      <Maturity journal={dossier.journal} />
      <Gaps dossier={dossier} />
    </div>
  );
}

function Heading({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h2
      id={id}
      className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500"
    >
      {children}
    </h2>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-[20px] border border-slate-200 bg-white p-5">
      {children}
    </div>
  );
}

/** A neutral marker. Deliberately one colour for every state: none of
    these vocabularies is ordered, and colouring them would invent a
    ranking the domain refuses. */
function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-slate-600">
      {children}
    </span>
  );
}

// ── 1. what am I looking at ─────────────────────────────────────────

/**
 * The archetype in investor language, with what it does *not* establish.
 *
 * `does_not_establish` is given equal weight to `rests_on` rather than
 * hidden in a footnote: an exchange network is not thereby a good one,
 * and the classification says so itself.
 */
function Identity({
  symbol,
  identity,
}: {
  symbol: string;
  identity: CryptoIdentity;
}) {
  return (
    <section aria-labelledby="identity-heading">
      <Heading id="identity-heading">What am I looking at</Heading>

      <div className="mt-3 rounded-[24px] border border-slate-200 bg-white p-6">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h1 className="text-2xl font-semibold text-slate-950">{symbol}</h1>
          <p className="text-lg text-slate-700">{identity.name}</p>
          <Tag>{identity.confidenceStated}</Tag>
        </div>

        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-700">
          {identity.explanation}
        </p>

        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-slate-600">
          <span className="font-semibold text-slate-800">
            Why this reading:{" "}
          </span>
          {identity.because}
        </p>

        <div className="mt-5 grid gap-5 sm:grid-cols-2">
          <List title="What this rests on" items={identity.restsOn} />
          <List
            title="What it does not establish"
            items={identity.doesNotEstablish}
          />
        </div>

        {identity.capabilities.length > 0 ? (
          <div className="mt-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Read through {identity.capabilities.length} lens
              {identity.capabilities.length === 1 ? "" : "es"}
            </p>
            <ul className="mt-2 space-y-1.5">
              {identity.capabilities.map((lens) => (
                <li key={lens.key} className="text-sm text-slate-700">
                  <span className="font-semibold">{lens.label}</span> — reads{" "}
                  {lens.reads}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {identity.alternatives.length > 0 ? (
          <div className="mt-5 border-t border-slate-100 pt-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Considered and not chosen
            </p>
            <ul className="mt-2 space-y-2">
              {identity.alternatives.map((item, index) => (
                <li key={`alt-${index}`} className="text-sm text-slate-600">
                  <span className="font-semibold text-slate-800">
                    {item.archetype}
                  </span>{" "}
                  — {item.notChosenBecause}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {identity.unmodelled.length > 0 ? (
          <div className="mt-5 rounded-[16px] bg-amber-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-900">
              Questions this kind of asset needs and this platform has not built
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-900">
              {identity.unmodelled.map((item, index) => (
                <li key={`unmodelled-${index}`}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {identity.notClassifiedFrom.length > 0 ? (
          <div className="mt-5 border-t border-slate-100 pt-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Evidence held and deliberately not classified from
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
              {identity.notClassifiedFrom.map((item, index) => (
                <li key={`refused-${index}`}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function List({ title, items }: { title: string; items: readonly string[] }) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
        {items.map((item, index) => (
          <li key={`${index}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

// ── 2. what can usefully be said ────────────────────────────────────

/**
 * The strongest useful statement per subject, and never stronger.
 *
 * The shapes are **not ordered** — a precise answer to a question the
 * investor is not asking is worth less than an honest bound on one they
 * are — so nothing here sorts, colours or ranks them.
 *
 * Where `whyItMatters` is empty and `interpretationWithheld` is set, the
 * measurement is shown and the refusal printed. **That is the point of
 * the section**: this platform can hold a number and not have
 * established what it means for this asset, and the two are different
 * claims.
 */
function Assessment({
  assessment,
}: {
  assessment: CryptoDossier["assessment"];
}) {
  return (
    <section aria-labelledby="assessment-heading">
      <Heading id="assessment-heading">What can usefully be said</Heading>

      <div className="mt-3 space-y-3">
        {assessment.statements.map((statement) => (
          <Statement key={statement.subject} statement={statement} />
        ))}

        {assessment.silentAbout.length > 0 ? (
          <Card>
            <p className="text-sm text-slate-600">
              <span className="font-semibold text-slate-800">
                Nothing useful is held about:{" "}
              </span>
              {assessment.silentAbout.join(", ")}.
            </p>
          </Card>
        ) : null}
      </div>
    </section>
  );
}

function Statement({ statement }: { statement: InvestorStatementView }) {
  return (
    <Card>
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-semibold text-slate-900">{statement.subject}</h3>
        <Tag>{statement.shapeStated}</Tag>
      </div>

      <p className="mt-2 text-[15px] leading-relaxed text-slate-800">
        {statement.stated}
      </p>

      {statement.qualification ? (
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          {statement.qualification}
        </p>
      ) : null}

      {statement.uncertainty ? (
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          <span className="font-semibold">Still open: </span>
          {statement.uncertainty}
        </p>
      ) : null}

      {statement.whyItMatters.map((meaning, index) => (
        <div
          key={`${meaning.question}-${index}`}
          className="mt-3 border-l-2 border-slate-200 pl-3"
        >
          <p className="text-sm leading-relaxed text-slate-700">
            {meaning.stated}
          </p>
          <p className="mt-1 text-xs leading-relaxed text-slate-500">
            {meaning.question} — {meaning.licensedBy}
          </p>
        </div>
      ))}

      {statement.interpretationWithheld ? (
        <div className="mt-3 rounded-[14px] bg-slate-50 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            What this means for this asset is not established here
          </p>
          <p className="mt-1.5 text-sm leading-relaxed text-slate-600">
            {statement.interpretationWithheld}
          </p>
        </div>
      ) : null}

      {statement.observed.length > 0 ? (
        <ul className="mt-3 space-y-0.5">
          {statement.observed.map((value, index) => (
            <li
              key={`${value.source}-${index}`}
              className="font-mono text-xs text-slate-500"
            >
              {value.source}: {value.value.toLocaleString()} {value.unit}
            </li>
          ))}
        </ul>
      ) : null}
    </Card>
  );
}

// ── 3. the committees ───────────────────────────────────────────────

/**
 * What each committee concluded, side by side. **Nothing is combined.**
 *
 * No overall verdict, no agreement, no score, no ranking, and confidence
 * is never compared across committees — two committees answering
 * different structural questions are not two votes on one proposition.
 * Each block leads with the committee's *question*, because a heading of
 * "Supply Governance" alone tells a reader nothing about what the answer
 * beneath it means.
 */
function Committees({
  committees,
}: {
  committees: readonly CommitteeCellView[];
}) {
  return (
    <section aria-labelledby="committees-heading">
      <Heading id="committees-heading">
        What each committee concluded — separately
      </Heading>

      <p className="mt-2 max-w-3xl text-sm text-slate-500">
        Each committee owns one question and answers it in its own words. They
        are shown beside one another and never combined: there is no overall
        verdict, no agreement and no score, because two different structural
        questions are not two votes on one proposition.
      </p>

      <div className="mt-3 space-y-3">
        {committees.length === 0 ? (
          <Card>
            <p className="text-sm text-slate-600">
              No committee has recorded a judgment for this asset.
            </p>
          </Card>
        ) : null}

        {committees.map((cell) => (
          <Card key={cell.key}>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-semibold text-slate-900">{cell.name}</h3>
              <Tag>{cell.applicability.replace(/_/g, " ")}</Tag>
            </div>

            {cell.question ? (
              <p className="mt-1.5 text-sm italic leading-relaxed text-slate-600">
                {cell.question}
              </p>
            ) : null}

            <p className="mt-3 text-[15px] leading-relaxed text-slate-800">
              {cell.verdictStated ?? cell.postureStated}
            </p>

            {cell.because ? (
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                {cell.because}
              </p>
            ) : null}

            {cell.unavailableBecause ? (
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                {cell.unavailableBecause}
              </p>
            ) : null}

            {cell.wordingRefused ? (
              <p className="mt-2 text-sm leading-relaxed text-amber-800">
                The committee&rsquo;s drafted explanation was refused by this
                platform&rsquo;s own checks, so the account above is its own.
              </p>
            ) : null}

            <dl className="mt-4 flex flex-wrap gap-x-8 gap-y-2 border-t border-slate-100 pt-3 text-xs text-slate-500">
              {cell.economicRole ? (
                <Detail label="Economic role read from">
                  {cell.economicRole}
                </Detail>
              ) : null}
              {cell.confidenceStated ? (
                <Detail label="Confidence, in its own terms">
                  {cell.confidenceStated}
                </Detail>
              ) : null}
              <Detail label="Evidence it weighed">
                {cell.evidenceCount} finding
                {cell.evidenceCount === 1 ? "" : "s"}
              </Detail>
              <Detail label="Times convened">{cell.judgmentsRecorded}</Detail>
            </dl>
          </Card>
        ))}
      </div>
    </section>
  );
}

function Detail({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <dt className="uppercase tracking-wide">{label}</dt>
      <dd className="mt-0.5 font-semibold text-slate-700">{children}</dd>
    </div>
  );
}

// ── 4. the questions this asset is asked ────────────────────────────

/**
 * Which questions apply, which are refused, and what came of each.
 *
 * The three groups are separated rather than sorted, because they are
 * different kinds of claim: *asked* is about the asset, *not applicable*
 * is about the question being the wrong instrument, and *undetermined*
 * is about this platform not knowing what the asset is. Flattened into
 * one list they would read as degrees of coverage.
 *
 * **`NOT_APPLICABLE` is never rendered as a negative result** and the
 * unanswered are never rendered as zeroes.
 */
function Questions({
  identity,
  quality,
}: {
  identity: CryptoIdentity;
  quality: QualityView | null;
}) {
  const asked = identity.questions.filter((q) => q.applicability === "ask");
  const refused = identity.questions.filter(
    (q) => q.applicability === "not_applicable_for_archetype",
  );
  const undetermined = identity.questions.filter(
    (q) => q.applicability === "undetermined",
  );

  const participation = new Map(
    (quality?.answers ?? []).map((answer) => [answer.key, answer]),
  );

  return (
    <section aria-labelledby="questions-heading">
      <Heading id="questions-heading">
        The questions this asset is asked
      </Heading>

      {quality ? (
        <div className="mt-3 rounded-[20px] border border-slate-200 bg-slate-50 p-5">
          <p className="text-sm font-semibold text-slate-800">
            Asset quality: {quality.quality}
          </p>
          <p className="mt-1.5 max-w-3xl text-sm leading-relaxed text-slate-600">
            {quality.because}
          </p>
          <p className="mt-3 text-xs text-slate-500">
            {quality.coverage.inScope} question
            {quality.coverage.inScope === 1 ? "" : "s"} in scope ·{" "}
            {quality.coverage.scorable} this platform can score at all ·{" "}
            {quality.coverage.answered} answered · {quality.coverage.shown}{" "}
            carrying evidence that is shown and not scored
          </p>
        </div>
      ) : null}

      <div className="mt-4 space-y-6">
        <QuestionGroup
          title={`Asked — ${asked.length}`}
          blurb="The archetype makes these meaningful for this asset."
          questions={asked}
          participation={participation}
        />

        {refused.length > 0 ? (
          <QuestionGroup
            title={`Not the right question — ${refused.length}`}
            blurb="Refused because they are the wrong instrument for this kind of asset. This is a claim about the question, not a mark against the asset."
            questions={refused}
            participation={participation}
          />
        ) : null}

        {undetermined.length > 0 ? (
          <QuestionGroup
            title={`Undetermined — ${undetermined.length}`}
            blurb="No archetype was established, so this platform cannot say whether these apply. A statement about what has been read here, never about the asset."
            questions={undetermined}
            participation={participation}
          />
        ) : null}
      </div>
    </section>
  );
}

function QuestionGroup({
  title,
  blurb,
  questions,
  participation,
}: {
  title: string;
  blurb: string;
  questions: readonly CryptoQuestionView[];
  participation: Map<string, QualityView["answers"][number]>;
}) {
  if (questions.length === 0) {
    return null;
  }

  return (
    <div>
      <p className="text-sm font-semibold text-slate-800">{title}</p>
      <p className="mt-1 max-w-3xl text-sm text-slate-500">{blurb}</p>

      <ul className="mt-3 space-y-2">
        {questions.map((question) => {
          const answer = participation.get(question.key);

          return (
            <li
              key={question.key}
              className="rounded-[16px] border border-slate-200 bg-white p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold text-slate-900">
                  {question.label}
                </span>
                {answer ? <Tag>{answer.participationStated}</Tag> : null}
              </div>

              <p className="mt-1 text-sm text-slate-600">{question.asks}</p>

              {answer?.stated ? (
                <p className="mt-2 text-sm leading-relaxed text-slate-800">
                  {answer.stated}
                </p>
              ) : null}

              {answer?.shown.map((line, position) => (
                <p
                  key={`shown-${position}`}
                  className="mt-1.5 text-sm text-slate-600"
                >
                  {line}
                </p>
              ))}

              <p className="mt-2 text-xs leading-relaxed text-slate-500">
                {question.applicabilityBecause}
              </p>

              {answer?.because ? (
                <p className="mt-1.5 text-xs leading-relaxed text-slate-500">
                  {answer.because}
                </p>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ── 5. supply ───────────────────────────────────────────────────────

/**
 * What each supply number counts, kept apart.
 *
 * Five distinct concepts, each with whose definition produced it. They
 * are not collapsed into a single "supply" figure, because a maximum, a
 * total emitted and a circulating estimate under somebody's methodology
 * are three different facts — and two of them only conflict if they
 * claim to represent the same thing.
 */
function Supply({
  supply,
  issuance,
}: {
  supply: SupplyView | null;
  issuance: IssuanceView | null;
}) {
  if (!supply && !issuance) {
    return null;
  }

  return (
    <section aria-labelledby="supply-heading">
      <Heading id="supply-heading">Supply, and what is still to come</Heading>

      {supply ? (
        <div className="mt-3 space-y-2">
          {supply.figures.map((figure, index) => (
            <Card key={`${figure.concept}-${figure.source}-${index}`}>
              <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {figure.conceptStated}
                </span>
                <span className="text-[15px] font-semibold text-slate-900">
                  {figure.stated}
                </span>
              </div>

              <p className="mt-1.5 text-sm text-slate-600">
                {figure.definedBy} {figure.methodology}
              </p>

              <p className="mt-1.5 text-xs text-slate-500">
                {figure.standingStated} · {figure.authorityStated}
                {figure.age ? ` · ${figure.age}` : ""}
              </p>

              {figure.caveats.map((caveat, index) => (
                <p
                  key={`fig-caveat-${index}`}
                  className="mt-1.5 text-xs text-amber-800"
                >
                  {caveat}
                </p>
              ))}
            </Card>
          ))}

          {supply.comparisons.map((comparison, index) => (
            <Card
              key={`${comparison.leftSource}-${comparison.rightSource}-${index}`}
            >
              <p className="text-sm font-semibold text-slate-800">
                {comparison.verdictStated}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                {comparison.leftSource}: {comparison.leftStated} ·{" "}
                {comparison.rightSource}: {comparison.rightStated}
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-600">
                {comparison.because}
              </p>
            </Card>
          ))}

          {supply.unresolved.length > 0 ? (
            <Card>
              <List title="Not resolved" items={supply.unresolved} />
            </Card>
          ) : null}

          {supply.unavailableBecause ? (
            <Card>
              <p className="text-sm text-slate-600">
                {supply.unavailableBecause}
              </p>
            </Card>
          ) : null}
        </div>
      ) : null}

      {issuance ? <Issuance issuance={issuance} /> : null}
    </section>
  );
}

function Issuance({ issuance }: { issuance: IssuanceView }) {
  return (
    <div className="mt-4 rounded-[20px] border border-slate-200 bg-white p-5">
      <p className="text-sm font-semibold text-slate-800">
        How new supply enters — {issuance.mechanismStated}
      </p>
      <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-600">
        {issuance.mechanismDescribed}.
      </p>

      <p className="mt-3 font-mono text-xs leading-relaxed text-slate-700">
        {issuance.formula}
      </p>

      <ul className="mt-3 space-y-1.5">
        {issuance.parameters.map((parameter) => (
          <li key={parameter.name} className="text-sm text-slate-600">
            <span className="font-semibold text-slate-800">
              {parameter.name}
            </span>{" "}
            {parameter.value.toLocaleString()} {parameter.unit} —{" "}
            {parameter.means}{" "}
            <span className="text-slate-400">
              (read from {parameter.readFrom})
            </span>
          </li>
        ))}
      </ul>

      <div className="mt-4 border-t border-slate-100 pt-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          What could change it — {issuance.mutabilityStated}
        </p>
        <p className="mt-1 text-sm leading-relaxed text-slate-600">
          {issuance.mutabilityBecause}
        </p>
      </div>

      {issuance.path.length > 0 ? (
        <div className="mt-4 border-t border-slate-100 pt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Under the currently observed policy
          </p>
          <p className="mt-1 text-sm text-slate-600">
            This platform&rsquo;s arithmetic from the rule above — not a
            forecast and not an observation. It holds while the rule does.
          </p>
          <ul className="mt-2 space-y-1">
            {issuance.path.map((step, index) => (
              <li
                key={`${step.horizon}-${index}`}
                className="font-mono text-xs text-slate-600"
              >
                {step.horizon}: {step.issuance.toLocaleString()} {step.unit}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {issuance.caveats.map((caveat, index) => (
        <p key={`caveat-${index}`} className="mt-2 text-xs text-amber-800">
          {caveat}
        </p>
      ))}
    </div>
  );
}

// ── 6. market ───────────────────────────────────────────────────────

function Market({ market }: { market: MarketView | null }) {
  if (!market) {
    return null;
  }

  return (
    <section aria-labelledby="market-heading">
      <Heading id="market-heading">The market it trades in</Heading>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <Card>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            This asset
          </p>
          <ul className="mt-2 space-y-1.5">
            {market.returns.map((item, index) => (
              <li
                key={`${item.label}-${index}`}
                className="text-sm text-slate-700"
              >
                <span className="font-semibold">{item.label}</span>{" "}
                {item.stated ?? "not held"}{" "}
                <span className="text-slate-400">({item.intervalStated})</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            The environment
          </p>
          <ul className="mt-2 space-y-1.5">
            {market.market.map((item, index) => (
              <li
                key={`${item.label}-${index}`}
                className="text-sm text-slate-700"
              >
                <span className="font-semibold">{item.label}</span>{" "}
                {item.stated ?? "not held"}
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {market.peerName ? (
        <Card>
          <p className="mt-3 text-sm font-semibold text-slate-800">
            Compared against {market.peerName}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            {market.peerSelectedBecause}
          </p>
          {market.relative.map((item, index) => (
            <p
              key={`${item.comparator}-${index}`}
              className="mt-2 text-sm text-slate-700"
            >
              {item.stated}
              {item.caveat ? (
                <span className="block text-xs text-slate-500">
                  {item.caveat}
                </span>
              ) : null}
            </p>
          ))}
          {market.peerCaveats.map((caveat, index) => (
            <p key={`${index}`} className="mt-1.5 text-xs text-slate-500">
              {caveat}
            </p>
          ))}
        </Card>
      ) : null}

      {market.peerUnavailableBecause ? (
        <Card>
          <p className="mt-3 text-sm text-slate-600">
            {market.peerUnavailableBecause}
          </p>
        </Card>
      ) : null}
    </section>
  );
}

// ── 7. what is happening ────────────────────────────────────────────

/**
 * What changed, what may be driving it, and what to watch.
 *
 * **Every claim shows its epistemic type**, because a provider's
 * "inflows are supporting BTC" is a reported flow plus an attributed
 * causal link, and printing the two alike publishes an opinion as a
 * measurement. An event's facts and the interpretations made of it are
 * rendered as two different things, and every interpretation carries
 * the name of whoever made it.
 */
function Happening({
  intelligence,
}: {
  intelligence: IntelligenceView | null;
}) {
  if (!intelligence) {
    return null;
  }

  return (
    <section aria-labelledby="happening-heading">
      <Heading id="happening-heading">What is happening</Heading>

      {intelligence.thinBecause ? (
        <Card>
          <p className="mt-3 text-sm text-slate-600">
            {intelligence.thinBecause}
          </p>
        </Card>
      ) : null}

      {intelligence.drivers.length > 0 ? (
        <div className="mt-3 space-y-2">
          {intelligence.drivers.map((driver, index) => (
            <Card key={`driver-${index}`}>
              <div className="flex flex-wrap items-center gap-2">
                <Tag>{driver.directionStated}</Tag>
                <Tag>{driver.supportStated}</Tag>
              </div>
              <p className="mt-2 text-[15px] leading-relaxed text-slate-800">
                {driver.stated}
              </p>
              {driver.mattersBecause ? (
                <p className="mt-1.5 text-sm leading-relaxed text-slate-600">
                  {driver.mattersBecause}
                </p>
              ) : null}
              <p className="mt-2 font-mono text-[11px] text-slate-400">
                rests on {driver.claims.join(", ")}
              </p>
            </Card>
          ))}
        </div>
      ) : null}

      {intelligence.events.length > 0 ? (
        <div className="mt-4">
          <p className="text-sm font-semibold text-slate-800">Developments</p>
          <div className="mt-2 space-y-2">
            {intelligence.events.map((event, index) => (
              <Card key={`event-${index}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <Tag>{event.family.replace(/_/g, " ")}</Tag>
                  {event.isMultiSource ? (
                    <Tag>independently carried</Tag>
                  ) : null}
                  {event.age ? (
                    <span className="text-xs text-slate-400">{event.age}</span>
                  ) : null}
                </div>

                <p className="mt-2 text-[15px] leading-relaxed text-slate-800">
                  {event.headline}
                </p>

                {event.facts.length > 0 ? (
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                    {event.facts.map((fact, position) => (
                      <li key={`fact-${position}`}>{fact.stated}</li>
                    ))}
                  </ul>
                ) : null}

                {event.interpretations.length > 0 ? (
                  <div className="mt-3 rounded-[14px] bg-slate-50 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      What sources read into it
                    </p>
                    <ul className="mt-1.5 space-y-1 text-sm text-slate-600">
                      {event.interpretations.map((reading, position) => (
                        <li key={`reading-${position}`}>
                          &ldquo;{reading.stated}&rdquo; — {reading.source}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <p className="mt-2 text-xs text-slate-400">
                  {event.sources.join(", ")}
                </p>
              </Card>
            ))}
          </div>
        </div>
      ) : null}

      {intelligence.claims.length > 0 ? (
        <div className="mt-4">
          <p className="text-sm font-semibold text-slate-800">
            What this rests on
          </p>
          <ul className="mt-2 space-y-1.5">
            {intelligence.claims.map((claim) => (
              <li
                key={claim.ref}
                className="rounded-[14px] border border-slate-200 bg-white px-4 py-2.5"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-[11px] text-slate-400">
                    {claim.ref}
                  </span>
                  <Tag>{claim.claimTypeStated}</Tag>
                  <span className="text-xs text-slate-400">
                    {claim.relevanceStated}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-700">{claim.stated}</p>
                <p className="mt-0.5 text-xs text-slate-400">
                  {claim.source}
                  {claim.age ? ` · ${claim.age}` : ""}
                </p>
                {claim.doesNotEstablish ? (
                  <p className="mt-1 text-xs text-slate-500">
                    Does not establish: {claim.doesNotEstablish}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {intelligence.watchNext.length > 0 ? (
        <div className="mt-4">
          <p className="text-sm font-semibold text-slate-800">Watch next</p>
          <ul className="mt-2 space-y-1.5">
            {intelligence.watchNext.map((item, index) => (
              <li key={`watch-${index}`} className="text-sm text-slate-700">
                <span className="font-semibold">{item.stated}</span>{" "}
                <span className="text-slate-500">
                  — measured by {item.measuredBy}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

// ── 8. how long this platform has been looking ──────────────────────

/**
 * Coverage before any finding.
 *
 * **A count of captures is never presented as a duration of
 * monitoring.** Every span sentence is the backend's own wording, and
 * this page renders it rather than computing a period from two dates —
 * which is precisely the sentence the journal layer forbids.
 */
function Maturity({ journal }: { journal: JournalView | null }) {
  if (!journal) {
    return (
      <section aria-labelledby="maturity-heading">
        <Heading id="maturity-heading">How long this has been watched</Heading>
        <Card>
          <p className="mt-3 text-sm text-slate-600">
            Nothing has been captured for this asset yet, so there is no
            observed history to read. That is a statement about this platform
            rather than about the asset.
          </p>
        </Card>
      </section>
    );
  }

  return (
    <section aria-labelledby="maturity-heading">
      <Heading id="maturity-heading">How long this has been watched</Heading>

      <div className="mt-3 rounded-[20px] border border-slate-200 bg-slate-50 p-5">
        <p className="text-sm font-semibold text-slate-800">
          {journal.captures} capture{journal.captures === 1 ? "" : "s"} recorded
        </p>
        <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-600">
          Every sentence below is worded from how often this platform actually
          looked. A count of captures is not a duration of monitoring, and
          nothing here presents it as one.
        </p>
      </div>

      <ul className="mt-3 space-y-2">
        {journal.facts.map((fact) => (
          <li
            key={fact.key}
            className="rounded-[16px] border border-slate-200 bg-white px-4 py-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Tag>{fact.statusStated}</Tag>
              <span className="text-xs text-slate-400">{fact.span.stated}</span>
            </div>
            <p className="mt-1.5 text-sm text-slate-700">{fact.stated}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

// ── 9. what is not known ────────────────────────────────────────────

/**
 * Every gap, collected where an investor can see them together.
 *
 * The section exists so *"bad"* and *"we do not know"* can be told
 * apart. Each line is assembled from a field the backend already sent —
 * this page selects and groups, and words nothing.
 */
function Gaps({ dossier }: { dossier: CryptoDossier }) {
  const withheld = dossier.assessment.statements
    .filter((statement) => statement.interpretationWithheld)
    .map((statement) => statement.subject);

  const unanswered = (dossier.quality?.answers ?? [])
    .filter((answer) => answer.participation === "unanswerable")
    .map((answer) => answer.label);

  const abstained = dossier.committees.committees
    .filter((cell) => !cell.verdict)
    .map((cell) => `${cell.name}: ${cell.postureStated}`);

  const conflicts = [
    ...(dossier.supply?.unresolved ?? []),
    ...(dossier.intelligence?.conflicting ?? []),
  ];

  const unread = dossier.intelligence?.surfacesUnread ?? [];

  return (
    <section aria-labelledby="gaps-heading">
      <Heading id="gaps-heading">What is not known</Heading>

      <p className="mt-2 max-w-3xl text-sm text-slate-500">
        Collected so that an unfavourable finding and an absent one can be told
        apart. Nothing here is a mark against the asset.
      </p>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <Card>
          <List
            title="Held, but nobody has established what it means here"
            items={withheld}
          />
          {withheld.length === 0 ? (
            <p className="text-sm text-slate-500">
              Every measurement shown carries a licensed interpretation.
            </p>
          ) : null}
        </Card>

        <Card>
          <List title="Applicable and unanswered" items={unanswered} />
          {unanswered.length === 0 ? (
            <p className="text-sm text-slate-500">
              No applicable question is left unanswered for want of evidence.
            </p>
          ) : null}
        </Card>

        <Card>
          <List title="Committees that reached no verdict" items={abstained} />
          {abstained.length === 0 ? (
            <p className="text-sm text-slate-500">
              Every registered committee answered.
            </p>
          ) : null}
        </Card>

        <Card>
          <List title="Readings that disagree" items={conflicts} />
          {conflicts.length === 0 ? (
            <p className="text-sm text-slate-500">
              No unresolved disagreement between sources.
            </p>
          ) : null}
        </Card>

        {dossier.assessment.silentAbout.length > 0 ? (
          <Card>
            <List
              title="Subjects nothing useful is held about"
              items={dossier.assessment.silentAbout}
            />
          </Card>
        ) : null}

        {unread.length > 0 ? (
          <Card>
            <List
              title="Surfaces this platform could not read"
              items={unread}
            />
          </Card>
        ) : null}
      </div>

      <p className="mt-4 flex items-start gap-2 text-xs leading-relaxed text-slate-500">
        <CircleAlert aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
        <span>
          Nothing on this page is a recommendation, a score or a ranking. This
          platform recommends; the investor decides — and for digital assets it
          does not yet recommend at all.
        </span>
      </p>
    </section>
  );
}
