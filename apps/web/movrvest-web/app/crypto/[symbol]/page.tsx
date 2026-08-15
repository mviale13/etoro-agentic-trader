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
  type FactsView,
  type IntelligenceView,
  type ProtocolFactView,
  type ProtocolView,
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
      <Committees
        committees={dossier.committees.committees}
        protocol={dossier.protocol}
      />
      <Questions identity={dossier.identity} quality={dossier.quality} />
      {dossier.protocol ? (
        <ProtocolEconomics protocol={dossier.protocol} symbol={dossier.symbol} />
      ) : null}
      <Supply supply={dossier.supply} issuance={dossier.issuance} />
      <Market market={dossier.market} />
      {dossier.facts ? (
        <JudgedFacts facts={dossier.facts} symbol={dossier.symbol} />
      ) : null}
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
 *
 * **One semantic conclusion, one owner.** A statement quoting a
 * committee belongs to the committees section below, which renders the
 * same conclusion with the question it answers, its applicability, its
 * confidence and the magnitudes beneath it. Rendered here as well it was
 * a verbatim second copy — across all eight assets every committee
 * reason was byte-identical between the two, and seven of fourteen
 * answers were too. So this section owns what the evidence layer
 * establishes, and `fromCommittee` is the backend's own mark of which
 * is which. **Nothing is dropped**: every committee statement, and every
 * silence a committee owns, still renders — one section further down.
 */
function Assessment({
  assessment,
}: {
  assessment: CryptoDossier["assessment"];
}) {
  const owned = assessment.statements.filter(
    (statement) => statement.fromCommittee === null,
  );

  const silent = assessment.silentAbout.filter(
    (subject) => !assessment.silentCommittees.includes(subject),
  );

  return (
    <section aria-labelledby="assessment-heading">
      <Heading id="assessment-heading">What can usefully be said</Heading>

      {/* A licensed meaning names the question that licensed it and the
          lens that question is asked through, and the second half is the
          same sentence every time that lens appears — five renderings of
          two sentences on Bitcoin, across three supply figures. The
          meaning and its licensing question stay on every figure, which
          is what Invariant 10 asks for; the lens explanation is stated
          on its first appearance and referred to thereafter. */}
      <div className="mt-3 space-y-3">
        {owned.map((statement, index) => (
          <Statement
            key={statement.subject}
            statement={statement}
            lensesAlreadyExplained={
              new Set(
                owned
                  .slice(0, index)
                  .flatMap((earlier) =>
                    earlier.whyItMatters.map((meaning) => meaning.licensedBy),
                  ),
              )
            }
          />
        ))}

        {silent.length > 0 ? (
          <Card>
            <p className="text-sm text-slate-600">
              <span className="font-semibold text-slate-800">
                Nothing useful is held about:{" "}
              </span>
              {silent.join(", ")}.
            </p>
          </Card>
        ) : null}
      </div>
    </section>
  );
}

function Statement({
  statement,
  lensesAlreadyExplained,
}: {
  statement: InvestorStatementView;
  lensesAlreadyExplained: ReadonlySet<string>;
}) {
  // Extended as this statement's own meanings are laid out, because two
  // questions on one figure may be asked through one lens just as two
  // figures may be.
  const explained = new Set(lensesAlreadyExplained);

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

      {statement.whyItMatters.map((meaning, index) => {
        const first = !explained.has(meaning.licensedBy);

        explained.add(meaning.licensedBy);

        return (
          <div
            key={`${meaning.question}-${index}`}
            className="mt-3 border-l-2 border-slate-200 pl-3"
          >
            <p className="text-sm leading-relaxed text-slate-700">
              {meaning.stated}
            </p>
            <p className="mt-1 text-xs leading-relaxed text-slate-500">
              {meaning.question}
              {first ? ` — ${meaning.licensedBy}` : null}
            </p>
          </div>
        );
      })}

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
/**
 * The magnitudes behind an answered value-capture judgment.
 *
 * The committee's own question is *"does this network generate
 * evidenced fee activity, and does an evidenced mechanism capture some
 * of it for the token or its holders?"* — two quantities, named in the
 * question itself: what users pay, and what reaches holders. So this
 * shows those two metrics and no others. No ranking, no threshold, no
 * arithmetic, and no view about which figure matters most — the third
 * quantity in the family, protocol revenue, is left to the economics
 * section rather than repeated here.
 *
 * **Every mapped entity is shown**, so a venue and the chain it runs on
 * stay two systems: Hyperliquid's exchange earns three orders of
 * magnitude more than its L1, and collapsing them to a single pair of
 * figures would hide exactly the distinction the archetype was built to
 * keep.
 *
 * Two rules it exists to keep. It fires **only where the committee
 * answered** — an abstention dressed in figures would read as evidence
 * for a verdict nobody reached. And it is a *reference*, not a second
 * record: the full economics, every family and every absence, live in
 * their own section, and these two or three lines point at it.
 */
function JudgmentMagnitude({
  cell,
  protocol,
}: {
  cell: CommitteeCellView;
  protocol: ProtocolView | null;
}) {
  if (cell.key !== "value_capture" || cell.posture !== "answered" || !protocol) {
    return null;
  }

  const supporting = protocol.entities.flatMap((entity) =>
    entity.facts
      .filter(
        (fact) =>
          (fact.metric === "fees" || fact.metric === "holder_revenue") &&
          fact.stated !== null,
      )
      .map((fact) => ({ entity: entity.name, fact })),
  );

  if (supporting.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 border-t border-slate-100 pt-3">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        The magnitudes it read
      </p>

      <ul className="mt-2 space-y-1">
        {supporting.map(({ entity, fact }) => (
          <li
            key={`${entity}-${fact.metric}`}
            className="flex flex-wrap items-baseline gap-x-2 text-sm leading-6 text-slate-700"
          >
            <span className="font-semibold tabular-nums text-slate-900">
              {fact.stated}
            </span>

            <span>
              {fact.label.toLowerCase()}
              {fact.window ? ` over ${fact.window}` : ""} — {entity}
            </span>

            <Tag>{fact.standingStated}</Tag>
          </li>
        ))}
      </ul>

      <p className="mt-2 text-xs leading-5 text-slate-400">
        Shown here because the judgment rests on them. Every figure the
        systems behind this token publish, including the ones that are
        absent, is in the economics section above.
      </p>
    </div>
  );
}

function Committees({
  committees,
  protocol,
}: {
  committees: readonly CommitteeCellView[];
  protocol: ProtocolView | null;
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

              {/* A committee that has never run here holds no
                  applicability reading either — it did not decline the
                  question, it never reached it. */}
              {cell.applicability ? (
                <Tag>{cell.applicability.replace(/_/g, " ")}</Tag>
              ) : null}
            </div>

            {cell.question ? (
              <p className="mt-1.5 text-sm italic leading-relaxed text-slate-600">
                {cell.question}
              </p>
            ) : null}

            {/* Verdict where it answered, posture where it ran and did
                not, and the matrix's own sentence where it has recorded
                nothing at all. Never a fabricated verdict. */}
            <p className="mt-3 text-[15px] leading-relaxed text-slate-800">
              {cell.verdictStated ?? cell.postureStated ?? cell.cellStated}
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

            {/* Two counters used to sit here and neither was investment
                evidence.

                *Evidence it weighed* was not what its label said. The
                count is captured beside the judgment by the recording
                command, whether or not the committee ever received it —
                and a committee that declines a question returns before
                reading any evidence at all. Bitcoin's Value Capture
                declined the question as the wrong instrument and the
                counter read "3 findings", citing none of them. Where the
                committee did answer, the findings it cited are already
                below, in the magnitudes it read.

                *Times convened* counted runs of `movrvest judge`. Across
                all sixteen recorded series no verdict has ever changed;
                every variation is this platform's own judging flag being
                turned off and on, plus one refused draft. That is
                execution history, and it stays in the record and on
                `movrvest committees` — it was never a finding about the
                asset. */}
            {cell.economicRole || cell.confidenceStated ? (
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
              </dl>
            ) : null}

            <JudgmentMagnitude cell={cell} protocol={protocol} />
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
  const participation = new Map(
    (quality?.answers ?? []).map((answer) => [answer.key, answer]),
  );

  // Grouped by the domain's own `participation`, never by a rule this
  // side invents. Applicability decides *whether* a question is asked;
  // participation decides whether anything is yet held to answer it —
  // and those are the two questions an investor is actually asking.
  //
  // Where no quality reading exists the map is empty, and every asked
  // question falls to `unresolved`, which is what it is.
  const held = identity.questions.filter((question) => {
    const answer = participation.get(question.key);

    return (
      question.applicability === "ask" &&
      (answer?.participation === "scored" ||
        answer?.participation === "shown" ||
        answer?.participation === "outside")
    );
  });

  const unresolved = identity.questions.filter(
    (question) =>
      question.applicability === "ask" && !held.includes(question),
  );

  const refused = identity.questions.filter(
    (q) => q.applicability === "not_applicable_for_archetype",
  );
  const undetermined = identity.questions.filter(
    (q) => q.applicability === "undetermined",
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
          title={`Asked, and something is held — ${held.length}`}
          blurb="The archetype makes these meaningful for this asset, and evidence has been read for them."
          questions={held}
          participation={participation}
        />

        {/* Asked and unanswered is a fact about this platform's
            evidence. It stays open and stays counted — folding it away
            would let a gap read as an absence of gaps — but it is one
            line each, because there is nothing yet to read. */}
        {unresolved.length > 0 ? (
          <QuestionSummaryGroup
            title={`Asked, and not yet answerable — ${unresolved.length}`}
            blurb="The archetype makes these meaningful and nothing is held to answer them yet. A statement about this platform's evidence, never about the asset."
            questions={unresolved}
            participation={participation}
          />
        ) : null}

        {/* Refused questions are the largest group on most assets — ten
            of nineteen on Bitcoin — and each one says the same kind of
            thing: this is the wrong instrument. Collapsed rather than
            dropped: every reason is one click away, and the count is
            visible without opening anything. */}
        {refused.length > 0 ? (
          <QuestionSummaryGroup
            title={`Not the right question for this kind of asset — ${refused.length}`}
            blurb="Refused because they are the wrong instrument here. This is a claim about the question, not a mark against the asset."
            questions={refused}
            participation={participation}
            collapsed
          />
        ) : null}

        {undetermined.length > 0 ? (
          <QuestionSummaryGroup
            title={`Undetermined — ${undetermined.length}`}
            blurb="No archetype was established, so this platform cannot say whether these apply. A statement about what has been read here, never about the asset."
            questions={undetermined}
            participation={participation}
            collapsed
          />
        ) : null}
      </div>
    </section>
  );
}

/**
 * A group of questions there is nothing yet to read, listed rather than
 * expounded.
 *
 * Both kinds it serves say one thing each: *nothing is held for this
 * yet*, or *this is the wrong instrument*. Printed at full length they
 * were a third of the page — nineteen questions on Bitcoin, of which
 * one is scored — so the platform's largest voice was the sound of what
 * it cannot say.
 *
 * **Nothing is removed and no wording is changed.** Every question
 * keeps its name, its own question text, its state tag and its
 * backend-authored reason; `collapsed` decides only whether the reason
 * starts open. Counts stay in the heading, so a group cannot be
 * mistaken for an empty one.
 */
function QuestionSummaryGroup({
  title,
  blurb,
  questions,
  participation,
  collapsed = false,
}: {
  title: string;
  blurb: string;
  questions: readonly CryptoQuestionView[];
  participation: Map<string, QualityView["answers"][number]>;
  collapsed?: boolean;
}) {
  if (questions.length === 0) {
    return null;
  }

  // An asked question's reason is its lens's, shared with every other
  // question that lens asks; a refused or undetermined one's is its
  // own — eight distinct reasons across Bitcoin's ten refusals. The
  // backend already tells the two apart: `askedBy` names the lens on an
  // asked question and is null on every other, corpus-wide. So the
  // shared reason rises to the group and the distinct ones stay on
  // their rows, and neither case is decided here by reading a sentence.
  const shared = questions.every((question) => question.askedBy !== null);

  const row = (question: CryptoQuestionView) => {
    const answer = participation.get(question.key);

    return (
      <li
        key={question.key}
        className="rounded-[16px] border border-slate-200 bg-white px-4 py-3"
      >
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <span className="text-sm font-semibold text-slate-900">
            {question.label}
          </span>

          <span className="text-sm text-slate-500">{question.asks}</span>

          {answer ? <Tag>{answer.participationStated}</Tag> : null}
        </div>

        {shared ? null : (
          <p className="mt-1 text-xs leading-relaxed text-slate-500">
            {question.applicabilityBecause}
          </p>
        )}
      </li>
    );
  };

  const rows = shared ? (
    <div className="mt-3 space-y-5">
      {byLens(questions).map((group) => (
        <div key={group.lens || group.rows[0].key}>
          <LensNote lens={group.lens} because={group.because} />
          <ul className="mt-2 space-y-2">{group.rows.map(row)}</ul>
        </div>
      ))}
    </div>
  ) : (
    <ul className="mt-3 space-y-2">{questions.map(row)}</ul>
  );

  if (!collapsed) {
    return (
      <div>
        <p className="text-sm font-semibold text-slate-800">{title}</p>
        <p className="mt-1 max-w-3xl text-sm text-slate-500">{blurb}</p>
        {rows}
      </div>
    );
  }

  return (
    <details>
      <summary className="cursor-pointer text-sm font-semibold text-slate-800">
        {title}
      </summary>

      <p className="mt-1 max-w-3xl text-sm text-slate-500">{blurb}</p>

      {rows}
    </details>
  );
}

/**
 * Asked questions, gathered under the lens that asks them.
 *
 * **A lens explanation belongs where the lens applies, and that is the
 * lens — not every row that inherits it.** An asked question's
 * `applicabilityBecause` *is* its lens sentence, corpus-wide and without
 * exception, and there are at most five distinct ones per asset against
 * fifteen questions: Bitcoin printed two sentences nine times between
 * them, Hyperliquid five sentences fifteen times.
 *
 * The grouping is the backend's own. `askedBy` names the lens on every
 * asked question, and it maps one-to-one onto `applicabilityBecause`
 * across all eight assets — so this side groups by a field it was given
 * and never by comparing two sentences. Refused and undetermined
 * questions do not come through here: their reasons are genuinely
 * different from one another — eight distinct ones on Bitcoin — and
 * `QuestionSummaryGroup` keeps them per row.
 */
function byLens(
  questions: readonly CryptoQuestionView[],
): readonly { lens: string; because: string; rows: CryptoQuestionView[] }[] {
  const groups = new Map<
    string,
    { lens: string; because: string; rows: CryptoQuestionView[] }
  >();

  for (const question of questions) {
    // Null only ever accompanies a question that is not asked, and one
    // cannot reach here. Keyed on the question itself if it ever does,
    // so an ungrouped row renders alone rather than silently joining a
    // lens that does not ask it.
    const key = question.askedBy ?? `:${question.key}`;

    const group = groups.get(key);

    if (group) {
      group.rows.push(question);
    } else {
      groups.set(key, {
        lens: question.askedBy ?? "",
        because: question.applicabilityBecause,
        rows: [question],
      });
    }
  }

  return [...groups.values()];
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

      <div className="mt-3 space-y-5">
        {byLens(questions).map((group) => (
          <div key={group.lens || group.rows[0].key}>
            <LensNote lens={group.lens} because={group.because} />

            <ul className="mt-2 space-y-2">
              {group.rows.map((question) => {
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

                    <p className="mt-1 text-sm text-slate-600">
                      {question.asks}
                    </p>

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

                    {/* The applicability sentence is the lens's, and it
                        is stated once above. What stays here is whatever
                        the answer adds beyond it. */}
                    {answer?.because &&
                    answer.because !== question.applicabilityBecause ? (
                      <p className="mt-2 text-xs leading-relaxed text-slate-500">
                        {answer.because}
                      </p>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

/** The lens a group of questions is asked through, said once. */
function LensNote({ lens, because }: { lens: string; because: string }) {
  return (
    <div className="border-l-2 border-slate-200 pl-3">
      {lens ? (
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Asked through the {lens.toLowerCase()} lens
        </p>
      ) : null}
      <p className="mt-0.5 max-w-3xl text-xs leading-relaxed text-slate-500">
        {because}
      </p>
    </div>
  );
}

// ── 4b. the economics of the system behind the token ────────────────

/** The four economic families, in the order the argument runs. */
const FAMILIES: readonly { key: string; title: string; blurb: string }[] = [
  {
    key: "value_generation",
    title: "What the system earns",
    blurb: "What users pay to use it, and what the system keeps of that.",
  },
  {
    key: "holder_accrual",
    title: "What reaches the token",
    blurb:
      "The share of the above an evidenced mechanism directs to the token or its holders.",
  },
  {
    key: "activity",
    title: "How much is flowing through it",
    blurb: "Volume and open positions, as the provider measures them.",
  },
  {
    key: "capital",
    title: "What is committed to it",
    blurb: "Assets held in the system's own contracts.",
  },
];

/** One measured figure, with everything needed to check it. */
function ProtocolFact({ fact }: { fact: ProtocolFactView }) {
  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="text-sm text-slate-700">
          {fact.label}
          {fact.window ? (
            <span className="text-slate-500"> over {fact.window}</span>
          ) : null}
        </span>

        <span className="flex shrink-0 items-baseline gap-2">
          {fact.stated ? (
            <span className="text-sm font-semibold tabular-nums text-slate-900">
              {fact.stated}
            </span>
          ) : null}

          {/* Availability and standing answer different questions, so
              both words are shown. "Not applicable" is not a gap, and
              "unavailable on a free source" is not "absent". */}
          <Tag>{fact.stated ? fact.standingStated : fact.availabilityStated}</Tag>
        </span>
      </div>

      {fact.providerMethodology ? (
        <p className="mt-1 text-xs leading-5 text-slate-500">
          {fact.providerMethodology}
        </p>
      ) : null}

      {fact.stated === null && fact.because ? (
        <p className="mt-1 text-xs leading-5 text-slate-500">{fact.because}</p>
      ) : null}

      {fact.age ? (
        <p className="mt-0.5 text-xs text-slate-400">{fact.age}</p>
      ) : null}
    </div>
  );
}

/**
 * What the systems behind the token actually earn, and what reaches it.
 *
 * Served on this endpoint from the day it existed, parsed into a view
 * model with no `facts` field, and rendered by nothing — the second
 * half of the same boundary defect that hid the judged market facts.
 * The general dossier showed all of it.
 *
 * The order is the argument, not a table: what the system earns, then
 * what reaches the token, then how much flows through it and what is
 * committed to it. Hyperliquid earns $842.7k of fees over the observed
 * day and $534.9k is reported as reaching holders — two figures that
 * only mean something next to each other.
 *
 * **Entities are never collapsed.** A venue and the chain it runs on
 * are two economic systems; reading them as one put two Hyperliquid
 * entities 224× apart under a single name. Each carries its own
 * `mappingBasis` — the filer's or provider's own reason the entity's
 * economics belong to this token — because a shared name is not a
 * reason.
 *
 * No ratio is formed here, and none is formed anywhere: fees over
 * market value would be a valuation multiple, and this platform holds a
 * market value for HYPE that two sources put 50% apart.
 */
function ProtocolEconomics({
  protocol,
  symbol,
}: {
  protocol: ProtocolView;
  symbol: string;
}) {
  if (protocol.entities.length === 0) {
    return (
      <section aria-labelledby="protocol-heading">
        <Heading id="protocol-heading">The economics behind it</Heading>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">
          {protocol.unmappedBecause ??
            `No system behind ${symbol} is mapped to it on evidence this platform holds.`}
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby="protocol-heading">
      <Heading id="protocol-heading">The economics behind it</Heading>

      <p className="mt-2 max-w-3xl text-sm text-slate-500">
        What the systems behind {symbol} earn, and what reaches the token —
        evidence, not verdicts. Nothing here is called strong, healthy or
        expensive, and no figure is divided by another: a fee measured over a
        day against a market value is a valuation multiple, and that is a claim
        this platform does not make.
      </p>

      <div className="mt-3 space-y-3">
        {protocol.entities.map((entity) => (
          <Card key={entity.key}>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-semibold text-slate-900">{entity.name}</h3>
              <Tag>{entity.kind}</Tag>
              {entity.mappingSettled ? null : <Tag>mapping unsettled</Tag>}
            </div>

            <p className="mt-1.5 text-sm leading-relaxed text-slate-600">
              {entity.measures}
            </p>

            {/* Why this entity's economics are this token's at all. A
                shared name establishes nothing, so the reason is given
                the same weight as the figures it justifies. */}
            <p className="mt-2 border-l-2 border-slate-200 pl-3 text-sm leading-relaxed text-slate-600">
              {entity.mappingBasis}
            </p>

            <div className="mt-4 space-y-4">
              {FAMILIES.map((family) => {
                const facts = entity.facts.filter(
                  (fact) => fact.family === family.key,
                );

                if (facts.length === 0) {
                  return null;
                }

                return (
                  <div key={family.key}>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      {family.title}
                    </p>

                    <p className="mt-0.5 text-xs leading-5 text-slate-400">
                      {family.blurb}
                    </p>

                    <div className="mt-2 space-y-2.5">
                      {facts.map((fact) => (
                        <ProtocolFact key={fact.metric} fact={fact} />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        ))}
      </div>

      {protocol.derived.length > 0 ? (
        <div className="mt-3 space-y-2">
          {protocol.derived.map((figure) => (
            <Card key={figure.label}>
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <span className="text-sm text-slate-700">{figure.label}</span>
                <span className="text-sm font-semibold tabular-nums text-slate-900">
                  {figure.statedValue}
                </span>
              </div>

              <p className="mt-1 text-sm leading-relaxed text-slate-600">
                {figure.stated}
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                {figure.caveat}
              </p>
            </Card>
          ))}
        </div>
      ) : null}
    </section>
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

// ── 6b. what is measured, and how far it is trusted ─────────────────

/**
 * The figures the validation gate judged, with its judgment attached.
 *
 * These were served on this endpoint from the day it existed and
 * dropped at the parser, so the asset-class dossier — the surface built
 * for tokens — was the one hiding them. On HYPE that meant a market
 * value two sources put 50% apart, a circulating supply three sources
 * put 4.5× apart, and a provider claim wrong by a factor of 1.5 million,
 * none of it visible on the token's own page.
 *
 * Two rules this section keeps. **A conflict is not hidden behind a
 * value**: where sources disagree the gate serves no figure at all, and
 * the reason it serves none is the finding, printed at full size rather
 * than as a tooltip. And **a rejected claim is never a candidate
 * value**: the ledger sits apart from the rows, because those numbers
 * are evidence about a source, not readings of the asset.
 *
 * Everything is worded by the backend — value, standing, standing
 * sentence, source, age, reason. This groups and places.
 */
function JudgedFacts({
  facts,
  symbol,
}: {
  facts: FactsView;
  symbol: string;
}) {
  return (
    <section aria-labelledby="facts-heading">
      <Heading id="facts-heading">
        What is measured about it, and how far it is trusted
      </Heading>

      <p className="mt-2 max-w-3xl text-sm text-slate-500">
        Every figure is a provider observation that was judged before it
        was served: checked for identity, for its own arithmetic, and
        against the other sources. Where they disagree, no value is shown
        for {symbol} — the disagreement is the finding, and averaging it
        away would invent a number nobody published.
      </p>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {facts.groups.map((group) => (
          <Card key={group.title}>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              {group.title}
            </p>

            <dl className="mt-3 space-y-3">
              {group.rows.map((row) => (
                <div key={row.label}>
                  <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                    <dt className="text-sm text-slate-700">{row.label}</dt>

                    <dd className="flex shrink-0 items-baseline gap-2">
                      {row.stated ? (
                        <span className="text-sm font-semibold tabular-nums text-slate-900">
                          {row.stated}
                        </span>
                      ) : null}

                      <Tag>{row.standingStated}</Tag>
                    </dd>
                  </div>

                  {/* Always shown, for every state. The equity dossier
                      puts this in a hover title; a reader who never
                      hovers never learns that two sources disagree. */}
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {row.because}
                  </p>

                  {row.age ? (
                    <p className="mt-0.5 text-xs text-slate-400">{row.age}</p>
                  ) : null}
                </div>
              ))}
            </dl>
          </Card>
        ))}
      </div>

      {facts.rejected.length > 0 ? (
        <div className="mt-3 rounded-[20px] border border-slate-300 bg-slate-50 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Claims this platform refused ({facts.rejected.length})
          </p>

          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Kept rather than discarded, and kept out of the figures above:
            a claim that failed validation is evidence about the source
            that made it, never a reading of {symbol}.
          </p>

          <ul className="mt-3 space-y-2">
            {facts.rejected.map((statement) => (
              <li
                key={statement}
                className="flex gap-2.5 text-sm leading-relaxed text-slate-700"
              >
                <span
                  aria-hidden="true"
                  className="mt-2 size-1 shrink-0 rounded-full bg-slate-400"
                />

                <span>{statement}</span>
              </li>
            ))}
          </ul>
        </div>
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

  const shared = journal.sharedMaturity;

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

        {/* The maturity every finding shares, where the backend says
            they share one. Thirteen findings each ending "First observed
            on one capture." did not describe deeper history than this
            single line does — they described the same shallow history
            thirteen times, directly under a heading that had already
            said one capture exists. Where the findings differ, this is
            null and each keeps its own below. */}
        {shared ? (
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">
            {shared.stated}
          </p>
        ) : null}
      </div>

      <ul className="mt-3 space-y-2">
        {journal.facts.map((fact) => {
          // Spoken for by the line above only if the section has one and
          // this finding is among the findings it speaks for. An
          // unavailable reading never is: it carries no coverage clause,
          // and its own sentence says the failure was this platform's
          // rather than the asset's.
          const covered = shared !== null && fact.carriesSpan;

          return (
            <li
              key={fact.key}
              className="rounded-[16px] border border-slate-200 bg-white px-4 py-3"
            >
              {covered ? null : (
                <div className="mb-1.5 flex flex-wrap items-center gap-2">
                  <Tag>{fact.statusStated}</Tag>
                  <span className="text-xs text-slate-400">
                    {fact.span.stated}
                  </span>
                </div>
              )}

              <p className="text-sm text-slate-700">
                {covered ? fact.observedStated : fact.stated}
              </p>
            </li>
          );
        })}
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
