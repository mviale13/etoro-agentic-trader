"""One reading of a primary financial statement: an observation.

The knowledge platform's second acquisition, opened by a measured
demand: the first live decision reached `MONITOR` because filing-grade
financial facts did not exist, and the accepted assessment design fixed
the road — the primary statements enter through the same tabular chain
that earned trust on segment sizes, as their own stream with its own
measurements (`docs/architecture/FINANCIAL_STATEMENT_ACQUISITION.md`).

An observation here is one draw, exactly as a
`CompanyKnowledgeObservation` is: admissible, checked, and one of
several a quorum will hold. Nothing downstream consumes one directly —
what the platform serves is the consensus derived over the set, in
`app.domain.financial_statement_consensus`.

Deliberately its own stream, never pooled with the segment
observations. The two readings are shown different text — the
statement's tables against Item 1 and the discussion's — and a
consensus over readings of different strings would call the difference
instability, which is the rule that forced the segment stream's own
schema 10.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

from app.domain.evidence import normalised
from app.domain.primary_source import PrimarySource, SourceDocument
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import ReportedFigure, SourceTable


class StatementKind(StrEnum):
    """Which primary statement a reading was of.

    Three members now, and each one arrived the way the first did: a
    consumer's demand for its figures was measured, and the vocabulary
    grew to meet it. The balance sheet and the cash flow statement
    entered together because the four financial analysts' rule tables
    name figures from both — a current ratio is two balance-sheet
    lines, free cash flow is two cash-flow lines — and a demand that
    specific is what the door was left open for.

    The mechanism below is general and always was. What is deliberately
    not general is this list: a statement enters when something asks it
    a question, never because a taxonomy would be tidier complete.
    """

    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW_STATEMENT = "cash_flow_statement"


class StatementConcept(StrEnum):
    """One figure this platform asks a statement for.

    A concept is a contract, not a label: the statement it belongs to,
    declared in `CONCEPT_STATEMENT`; the question it asks, worded in
    `CONCEPT_QUESTIONS`; and the row labels this platform accepts as
    answering it, declared in `CONCEPT_LABELS` and grown only by a live
    refusal naming the label a real filer used. A reading cannot
    relabel a row into a concept, because the label check reads the
    document, never the reading.

    Every member below is here because a named consumer asks for it.
    `GROSS_PROFIT` and `OPERATING_INCOME` are the profitability
    analyst's two remaining margins; the two balance-sheet pairs are
    the balance-sheet analyst's two ratios; the two cash-flow lines are
    the cash-flow analyst's. Growth needs no concept at all — it is
    arithmetic along a row this platform already reads.

    What is deliberately *not* here is as considered as what is. No
    concept was added for return on equity or invested capital: no
    rule table asks for them today, and a concept acquired ahead of its
    consumer is the taxonomy-first move the door stays shut against.

    And no prudential concept is here — not CET1, not Tier 1 capital,
    not a regulatory leverage ratio, not the liquidity coverage ratio,
    not the NSFR — because no filer prints one on the face of a primary
    statement. Measured across the corpus in four jurisdictions: zero
    occurrences. They belong to a separate evidence domain sourced from
    a filing's regulatory sections, and adding one here would be
    inventing a location the documents do not have. The boundary is
    accepted: `docs/architecture/FINANCIAL_DOMAIN_BOUNDARY.md`.
    """

    TOTAL_REVENUE = "total_revenue"
    GROSS_PROFIT = "gross_profit"
    OPERATING_INCOME = "operating_income"
    NET_INCOME = "net_income"

    #: The two lines that say, positively, which financial language a
    #: statement is written in. They are not margins and no analyst
    #: scores them: their consumer is `StatementLanguage`, which needs
    #: *positive* evidence because the corpus proved absence cannot
    #: supply it — a filing printing no gross profit, no operating
    #: income and an unclassified balance sheet is equally a bank, an
    #: insurer and a section this platform failed to read
    #: (`docs/architecture/FINANCIAL_LANGUAGE_CORPUS.md`).
    #:
    #: Deliberately two, out of six candidates measured. Interest income
    #: and interest expense were refused: Coca-Cola, Tesla, Walmart and
    #: Procter & Gamble all print them, so they separate nothing.
    #: Claims, policyholder benefits and insurance reserves were refused
    #: for a different reason — five insurers print five different
    #: labels for them and Citigroup prints "Total provisions for credit
    #: losses and for benefits and claims", so there is no row to ground
    #: and a false positive waiting in the one bank that has insurance.
    NET_INTEREST_INCOME = "net_interest_income"
    PREMIUM_REVENUE = "premium_revenue"

    TOTAL_CURRENT_ASSETS = "total_current_assets"
    TOTAL_CURRENT_LIABILITIES = "total_current_liabilities"
    TOTAL_LIABILITIES = "total_liabilities"
    TOTAL_EQUITY = "total_equity"

    OPERATING_CASH_FLOW = "operating_cash_flow"
    CAPITAL_EXPENDITURES = "capital_expenditures"


#: Which statement prints each concept.
#:
#: The partition that keeps a reading honest: one reading is shown one
#: statement's tables and asked only that statement's concepts, so a
#: figure can never be located in a document region the concept does
#: not belong to. It is also what lets the consensus stay a property of
#: one statement — the rule `statement_consensus_of` enforces.
CONCEPT_STATEMENT: dict[StatementConcept, StatementKind] = {
    StatementConcept.TOTAL_REVENUE: StatementKind.INCOME_STATEMENT,
    StatementConcept.GROSS_PROFIT: StatementKind.INCOME_STATEMENT,
    StatementConcept.OPERATING_INCOME: StatementKind.INCOME_STATEMENT,
    StatementConcept.NET_INCOME: StatementKind.INCOME_STATEMENT,
    StatementConcept.NET_INTEREST_INCOME: StatementKind.INCOME_STATEMENT,
    StatementConcept.PREMIUM_REVENUE: StatementKind.INCOME_STATEMENT,
    StatementConcept.TOTAL_CURRENT_ASSETS: StatementKind.BALANCE_SHEET,
    StatementConcept.TOTAL_CURRENT_LIABILITIES: StatementKind.BALANCE_SHEET,
    StatementConcept.TOTAL_LIABILITIES: StatementKind.BALANCE_SHEET,
    StatementConcept.TOTAL_EQUITY: StatementKind.BALANCE_SHEET,
    StatementConcept.OPERATING_CASH_FLOW: StatementKind.CASH_FLOW_STATEMENT,
    StatementConcept.CAPITAL_EXPENDITURES: StatementKind.CASH_FLOW_STATEMENT,
}


def concepts_of(statement: StatementKind) -> tuple[StatementConcept, ...]:
    """The concepts this statement is asked for, in the vocabulary's order."""

    return tuple(
        concept
        for concept in StatementConcept
        if CONCEPT_STATEMENT[concept] is statement
    )


def statement_tables(
    document: SourceDocument, statement: StatementKind
) -> tuple[SourceTable, ...]:
    """The tables the filer printed under this statement's own title.

    The whole of what a reading of this statement is shown. Keeping the
    three statements' tables apart is not tidiness: a reading handed
    every table in Item 8 could locate "total revenue" on the cash flow
    statement's supplementary schedule and pass every check, because the
    checks prove where a figure is, never which statement it belongs to.
    """

    return {
        StatementKind.INCOME_STATEMENT: document.income_statement_tables,
        StatementKind.BALANCE_SHEET: document.balance_sheet_tables,
        StatementKind.CASH_FLOW_STATEMENT: document.cash_flow_tables,
    }[statement]


def statement_text(document: SourceDocument, statement: StatementKind) -> str:
    """The prose under that title, which says which absence an absence is.

    Read only to word a refusal: a statement whose title this platform
    never located and a located statement printing no readable table are
    different findings, and only the second is about the document.
    """

    return {
        StatementKind.INCOME_STATEMENT: document.income_statement_text,
        StatementKind.BALANCE_SHEET: document.balance_sheet_text,
        StatementKind.CASH_FLOW_STATEMENT: document.cash_flow_text,
    }[statement]


def statement_contenders(document: SourceDocument, statement: StatementKind) -> int:
    """How many places in the document could have opened this statement.

    One means the filing named the section once and the location is not
    in doubt. Several means the platform chose among structural
    contenders, and that choice is an interpretation nothing downstream
    has checked — so every figure read from the section carries it.
    """

    return {
        StatementKind.INCOME_STATEMENT: document.income_statement_contenders,
        StatementKind.BALANCE_SHEET: document.balance_sheet_contenders,
        StatementKind.CASH_FLOW_STATEMENT: document.cash_flow_contenders,
    }[statement]


#: What a filer calls each statement, for wording a refusal an investor
#: reads. The enum's own value is a machine key and reads like one.
STATEMENT_NAMES: dict[StatementKind, str] = {
    StatementKind.INCOME_STATEMENT: "income statement",
    StatementKind.BALANCE_SHEET: "balance sheet",
    StatementKind.CASH_FLOW_STATEMENT: "cash flow statement",
}


#: What each concept asks for, in words a refusal can carry.
#:
#: A balance sheet is dated rather than periodic, so its concepts ask
#: for the most recent *date* the statement reports. Which column that
#: is stays the reading's only positional claim, checkable by anyone
#: against the header stored beside the figure.
CONCEPT_QUESTIONS: dict[StatementConcept, str] = {
    StatementConcept.TOTAL_REVENUE: (
        "the company's total revenue for the most recent period the statement reports"
    ),
    StatementConcept.GROSS_PROFIT: (
        "the company's gross profit for the most recent period the statement "
        "reports, where the statement prints that line"
    ),
    StatementConcept.OPERATING_INCOME: (
        "the company's operating income for the most recent period the "
        "statement reports, where the statement prints that line"
    ),
    StatementConcept.NET_INCOME: (
        "the company's net income for the most recent period the statement reports"
    ),
    StatementConcept.NET_INTEREST_INCOME: (
        "the net interest income the statement reports for the most recent "
        "period — interest earned less interest paid, as a single line the "
        "statement prints — where the statement prints that line. Not a "
        "subtotal struck after it, such as net interest income after a "
        "provision for credit losses"
    ),
    StatementConcept.PREMIUM_REVENUE: (
        "the insurance premium revenue the statement reports for the most "
        "recent period, as a revenue line of the statement, where the "
        "statement prints that line. Not premiums written, and not a "
        "movement in unearned premiums — both are amounts other than the "
        "revenue the period earned"
    ),
    StatementConcept.TOTAL_CURRENT_ASSETS: (
        "the company's total current assets at the most recent date the "
        "balance sheet reports, where the balance sheet is classified"
    ),
    StatementConcept.TOTAL_CURRENT_LIABILITIES: (
        "the company's total current liabilities at the most recent date the "
        "balance sheet reports, where the balance sheet is classified"
    ),
    StatementConcept.TOTAL_LIABILITIES: (
        "the company's total liabilities at the most recent date the balance "
        "sheet reports"
    ),
    StatementConcept.TOTAL_EQUITY: (
        "the total equity attributable to the company's shareholders at the "
        "most recent date the balance sheet reports"
    ),
    StatementConcept.OPERATING_CASH_FLOW: (
        "the net cash the company generated from operating activities for the "
        "most recent period the statement reports"
    ),
    StatementConcept.CAPITAL_EXPENDITURES: (
        "the cash the company spent on purchases of property, plant and "
        "equipment for the most recent period the statement reports"
    ),
}

#: The row labels this platform reads as answering each concept,
#: compared after `normalised` so typography and case cannot decide.
#: Declared, deterministic, and deliberately short: every form here was
#: chosen because filers print it as the statement's own line, and a
#: label outside the list is refused with the filer's words in the
#: refusal — which is exactly the sentence that earns the next entry.
CONCEPT_LABELS: dict[StatementConcept, tuple[str, ...]] = {
    StatementConcept.TOTAL_REVENUE: (
        "total net revenue",
        "total net revenues",
        "total revenue",
        "total revenues",
        "net revenues",
        "net revenue",
        "revenues",
        "revenue",
        "net sales",
        "total net sales",
        "total sales and revenues",
        "total revenues and other income",
        # Coca-Cola's top line, and earned by the filing's own
        # arithmetic rather than by containing the word *revenues*:
        # `Net Operating Revenues` 47,941 less `Cost of goods sold`
        # 18,397 is 29,544, which is exactly the `Gross Profit` the
        # statement prints on the next row. A component or a segment
        # stands in no such relation to the lines beneath it, which is
        # what separates this from `Mortgage banking revenues` and
        # `Wealth and asset management revenue` — both of which remain
        # refused (BQ11).
        "net operating revenues",
        # One more, on the same standard (BQ19). Union Pacific totals
        # `Freight revenues` 23,220 and `Other revenues` 1,290 to
        # 24,510 exactly — an addition of two revenue components with
        # no expense deducted, which is what makes it a gross top line
        # rather than a net one. It occurs once in the whole corpus.
        "total operating revenues",
        # Two further candidates were measured and **rejected**, each on
        # its own evidence rather than as a bundle.
        #
        # `total revenues net of interest expense` (American Express,
        # Citigroup) reconciles — and the reconciliation is the refusal:
        # 54,865 + 25,598 **− 8,234** = 72,229 subtracts an expense, so
        # the line is a different economic quantity from a consolidated
        # top line. BQ11 ruled exactly that and pinned it, and this
        # slice found no evidence to overturn it. *(The inconsistency
        # that Goldman's accepted `Total net revenues` is built the same
        # way is real, recorded in BQ19, and belongs to whichever slice
        # argues that ruling — not to a vocabulary widening.)*
        #
        # `total income` (Barclays, NatWest) reconciles too, and is
        # refused for a collision the sweep found: M&T prints the
        # identical phrase in a table titled *Condensed Statement of
        # Income*, where it totals `Dividends from consolidated
        # subsidiaries` 2,776 with interest of 116 to 2,916. That is the
        # parent company alone, against consolidated interest income of
        # 10,486. Only the concept-to-statement partition keeps the two
        # apart today, and that is a boundary rather than a property of
        # the label.
    ),
    StatementConcept.NET_INCOME: (
        "net income",
        "net income (loss)",
        "net earnings",
        "net earnings (loss)",
        "profit for the year",
        "profit for the period",
    ),
    StatementConcept.GROSS_PROFIT: (
        "gross profit",
        "gross margin",
        "gross profit (loss)",
    ),
    StatementConcept.OPERATING_INCOME: (
        "operating income",
        "operating income (loss)",
        "income from operations",
        "loss from operations",
        "operating profit",
        "total operating income",
        "operating income from continuing operations",
    ),
    #: One form, and the exactness is the whole contract. Ten of the
    #: eleven banks whose income statement this platform reads print
    #: "Net interest income" and six of them *also* print "Net interest
    #: income after provision for credit losses" directly beneath it —
    #: a different quantity, struck after an expense. Equality after
    #: `normalised` accepts the first and refuses the second, which is
    #: why no containment rule may ever be used here.
    StatementConcept.NET_INTEREST_INCOME: ("net interest income",),
    #: Two forms, because US filers print the earned-premium revenue
    #: line two ways: bare on a life or multiline insurer's statement
    #: (Travelers, MetLife, AIG) and named in full on a property and
    #: casualty one (Chubb).
    #:
    #: What is refused matters more. "Net premiums written" is not
    #: revenue — it is a production statistic printed immediately above
    #: the revenue line, and Chubb prints all three of written, the
    #: movement in unearned, and earned. "Preferred stock redemption
    #: premium" is not insurance at all, and MetLife and AIG both print
    #: it further down the same statement. Equality refuses each.
    #:
    #: Claimed for US GAAP filings only, because the corpus holds no
    #: IFRS insurer. An IFRS 17 filer prints "Insurance revenue", which
    #: is a differently-defined quantity and is deliberately not listed
    #: here: it would be flattening two accounting concepts because they
    #: are economically similar.
    StatementConcept.PREMIUM_REVENUE: (
        "premiums",
        "net premiums earned",
    ),
    StatementConcept.TOTAL_CURRENT_ASSETS: ("total current assets",),
    StatementConcept.TOTAL_CURRENT_LIABILITIES: ("total current liabilities",),
    StatementConcept.TOTAL_LIABILITIES: ("total liabilities",),
    #: Deliberately the equity attributable to the parent's shareholders,
    #: never "total equity including noncontrolling interests": the two
    #: are different quantities, and a ratio that silently mixed them
    #: across filers would compare companies on different denominators.
    #: A filer printing only the combined line is refused with its own
    #: words, which is what earns the next entry here.
    #: The bare forms were earned by a live refusal, which is the only
    #: way a form enters here. JPMorgan's balance sheet condenses equity
    #: to a single line labelled "Stockholders' equity" — 362,438 — and
    #: prints no "Total" anywhere near it, so the reading pointed at the
    #: right cell and this platform refused it for the filer's wording.
    #:
    #: Accepting the bare form does not let a section header in. On a
    #: filing that uses it as a heading over a breakdown, that row
    #: prints no number, and a cell that prints no number is already
    #: refused as measuring nothing before any label is compared.
    #:
    #: The form a filer builds out of its own name — "Total Allstate
    #: shareholders' equity" — is not listed and cannot be: it is one
    #: form per company. It is accepted by `names_its_own_equity`
    #: instead, which is a rule rather than a list, and which replaced
    #: an entry that had hard-coded one company's wording by name.
    StatementConcept.TOTAL_EQUITY: (
        "total stockholders' equity",
        "total stockholders equity",
        "total shareholders' equity",
        "total shareholders equity",
        "total shareowners' equity",
        "total common stockholders' equity",
        "stockholders' equity",
        "shareholders' equity",
        "shareowners' equity",
    ),
    StatementConcept.OPERATING_CASH_FLOW: (
        "net cash provided by operating activities",
        "net cash provided by (used in) operating activities",
        "net cash used in operating activities",
        "net cash from operating activities",
        "net cash provided by operating activities of continuing operations",
        "cash provided by operating activities",
        "net cash flows from operating activities",
        "net cash (used in) provided by operating activities",
    ),
    #: Printed as a negative in the statement, because it is cash out.
    #: Nothing here flips the sign: the printed cell is the fact, and the
    #: consumer that subtracts it says which direction it is subtracting.
    StatementConcept.CAPITAL_EXPENDITURES: (
        "purchases of property and equipment",
        "purchases of property, plant and equipment",
        "purchase of property and equipment",
        "purchase of property, plant and equipment",
        "payments for acquisition of property, plant and equipment",
        "capital expenditures",
        "additions to property, plant and equipment",
        "additions to property and equipment",
        "expenditures for property, plant and equipment",
    ),
}


#: A footnote marker a filer prints after a line's name: "(a)", "(1)".
#:
#: Bounded to one to three letters or digits inside brackets, which is
#: what keeps it from eating a parenthetical that is part of the name.
#: "Net income (loss)" carries four letters and survives; so does
#: "Gross profit (loss)". The distinction is not stylistic — "(loss)"
#: says what the line measures and "(a)" says where to read about it.
_FOOTNOTE = re.compile(r"\s*\((?:[a-z]{1,3}|\d{1,3})\)\s*$", re.IGNORECASE)


def without_footnote(label: str) -> str:
    """A row label with a trailing footnote marker removed.

    Earned by a live refusal, and by the one that proves the point: the
    audited balance sheet JPMorgan prints labels its line "Total
    liabilities (a)", where the summary of the same figures in the
    MD&A prints "Total liabilities". The marker is a pointer into the
    notes, not part of what the line is called — so a platform that
    read it as part of the name would refuse the audited statement and
    accept the discussion of it, which is precisely backwards.
    """

    return _FOOTNOTE.sub("", label.strip())


#: The words a filer uses for the people who own it.
_HOLDERS = frozenset({"stockholders", "shareholders", "shareowners"})

#: Words that, standing between "Total" and the equity phrase, prove the
#: row is *not* the parent's equity. "Total liabilities and stockholders'
#: equity" is the balance sheet's grand total and is many times larger;
#: reading it as equity would divide by the wrong number everywhere it is
#: used. Every one of these was taken off a real row in the corpus.
_NOT_THE_PARENTS = frozenset(
    {
        "liabilities",
        "liability",
        "and",
        "equity",
        "including",
        "noncontrolling",
        "redeemable",
        "mezzanine",
        "deficit",
        "temporary",
        "permanent",
        "preferred",
    }
)

#: Splits a label into words, unlike `normalised`, which removes the
#: spaces along with the punctuation. A rule about which words sit
#: *between* two others cannot be written on a form that has lost the
#: word boundaries — on `normalised` output, "total liabilities and
#: stockholders equity" and "total stockholders equity" differ only by
#: characters in the middle, and any bounded wildcard admits both.
_WORDS = re.compile(r"[^a-z0-9]+")


def _words(label: str) -> tuple[str, ...]:
    """A row label as its words, lowercased, punctuation dropped."""

    return tuple(word for word in _WORDS.split(label.casefold()) if word)


def names_its_own_equity(label: str) -> bool:
    """Whether this row is the parent's equity, stated with the filer's name.

    "Total Allstate shareholders' equity", "Total Honeywell shareowners'
    equity", "Total MetLife, Inc.'s stockholders' equity" — one form per
    company, so a list cannot hold them and a rule must.

    The rule is deliberately narrow, and reads as a shape rather than as
    a name: the row opens with *Total*, closes with a holder word and
    *equity*, and carries at least one word between them that is none of
    `_NOT_THE_PARENTS`. This platform never learns what a company calls
    itself — it only accepts that *something* stands where a name would.

    Measured against every row of all forty-four corpus filings, this
    accepts nine rows and every one is the parent's equity. It refuses
    every grand total in the corpus, including MetLife's "Total
    liabilities, mezzanine equity and equity", Walmart's "Total
    liabilities, redeemable noncontrolling interest, and shareholders'
    equity", and Barclays' "Total equity excluding non-controlling
    interests".
    """

    words = _words(without_footnote(label))

    if len(words) < 4:
        return False

    if words[0] != "total" or words[-1] != "equity" or words[-2] not in _HOLDERS:
        return False

    between = words[1:-2]

    return bool(between) and not (set(between) & _NOT_THE_PARENTS)


def matches_concept(concept: StatementConcept, label: str) -> bool:
    """Whether a filer's row label answers this concept.

    Equality after `normalised`, never containment. "Total net
    revenue" contains "revenue", and so does "Revenue from contracts
    with related parties" — a containment rule would read the second
    as the company's revenue. A declared form matches exactly or the
    cell is refused.

    A trailing footnote marker is removed before comparing, because it
    is typography rather than the line's name.

    One concept has a rule beside its list, and only because a list
    cannot express it: the parent's equity as a filer builds it out of
    its own name. `names_its_own_equity` states what that row looks
    like, and refuses everything else the same way an absent form does.
    """

    printed = normalised(without_footnote(label))

    if any(printed == normalised(form) for form in CONCEPT_LABELS[concept]):
        return True

    return concept is StatementConcept.TOTAL_EQUITY and names_its_own_equity(label)


def concept_vocabulary_fingerprint(concept: StatementConcept) -> str:
    """The identity of one concept's accepted vocabulary, as a value.

    The gap this closes was measured before it was named. The schema
    version says what a reading was *shown* and *asked*; it does not say
    which labels the reading was permitted to *accept* — `301cfdf`
    bundled a parser repair invisibly under the schema-3 bump, and
    `6c96ea0` widened `TOTAL_REVENUE` by one form under no bump at all.
    So two observations can share a schema and disagree about what an
    absence means: a pre-widening reading's *"no figure located for
    total_revenue"* was true under its vocabulary and is not a claim
    today's vocabulary would make of the same filing.

    A fingerprint over the normalised, sorted forms answers the transport
    question — *may these two readings participate in one consensus
    under today's interpretation?* — per concept, which matters because
    vocabulary moves one concept at a time: every concept but
    `TOTAL_REVENUE` is unchanged across the whole schema-3 corpus, and a
    per-vocabulary hash would incompatibilise absences the change never
    touched.

    Two honest limits, stated rather than hidden. `TOTAL_EQUITY` also
    accepts rows by `names_its_own_equity`, which is code and not a
    constant, so its fingerprint identifies the list and not the rule.
    And parse behaviour is not here at all — an anchor is checkable
    against the immutable document (the statement audit's approach), so
    the vocabulary is the one axis that is neither in the schema nor
    checkable from the record.
    """

    forms = sorted(normalised(form) for form in CONCEPT_LABELS[concept])

    digest = sha256("\n".join([concept.value, *forms]).encode("utf-8"))

    return digest.hexdigest()[:16]


def vocabulary_fingerprints() -> dict[str, str]:
    """Every concept's vocabulary identity, under the live contract."""

    return {
        concept.value: concept_vocabulary_fingerprint(concept)
        for concept in StatementConcept
    }


@dataclass(frozen=True, slots=True)
class ConceptContract:
    """The vocabulary one concept was read under, as the reading found it.

    A fact *about the producer*, stamped once when the observation is
    taken and never touched again. That is the whole point: BQ16 could
    only rule on the historical corpus through operator testimony —
    an authored manifest, reasoned from repository history — because the
    records themselves carried no trace of which labels their reader was
    permitted to accept. Everything taken from here on carries its own.
    """

    concept: StatementConcept

    #: `concept_vocabulary_fingerprint` at the moment of reading. The
    #: fingerprint, never the forms: a reader that stored the vocabulary
    #: itself would put a copy of `CONCEPT_LABELS` in every observation
    #: of every company, and the question this answers is only whether
    #: two contracts are the same one.
    fingerprint: str


def producing_contract(statement: StatementKind) -> tuple[ConceptContract, ...]:
    """The vocabulary identity of every concept this statement is asked.

    Called at acquisition, and only there. It reads the live
    `CONCEPT_LABELS` because at that instant the live contract *is* the
    producing contract — which is exactly why nothing on the read path
    may ever call it. See `FinancialStatementObservation.produced_under`.
    """

    return tuple(
        ConceptContract(
            concept=concept,
            fingerprint=concept_vocabulary_fingerprint(concept),
        )
        for concept in concepts_of(statement)
    )


@dataclass(frozen=True, slots=True)
class StatementFact:
    """One concept, either located and checked or absent with its reason.

    Two claims travel together when located, and they are not equals:

    - **The anchor** is what the reading asserted and this platform
      checked — the cell for the most recent period, read back out of
      the document and compared with what the reading said is there.
    - **The row** is what this platform then read for itself: every
      figure the anchored row prints under a named column, prior
      periods included, each carrying its header verbatim. No model
      claim stands anywhere in it.

    Which column is which period is never interpreted here. The
    headers say, in the filer's words, and a consumer that needs the
    period reads the header it stored.
    """

    concept: StatementConcept

    #: The checked cell, or None where nothing was located.
    anchor: ReportedFigure | None

    #: The anchored row as this platform read it, anchor's cell
    #: included. Empty exactly when the anchor is absent.
    row: tuple[ReportedFigure, ...] = ()

    #: Why there is no figure, in words. "The reading located no cell"
    #: and "this platform located no statement" are different facts,
    #: and only one of them is about the filing.
    unlocated_because: str | None = None

    @property
    def is_located(self) -> bool:
        """Whether the statement was shown to print this figure."""

        return self.anchor is not None


@dataclass(frozen=True, slots=True)
class FinancialStatementObservation:
    """One reading of one primary statement of one immutable document.

    Facts, never conclusions — and observed facts, never the settled
    account. Immutable once taken, for the same reason every
    observation is: correcting one would destroy the disagreement the
    consensus exists to measure.

    Carries one fact per concept, always: a concept that could not be
    located is present as a worded absence, so a reader never has to
    infer whether a missing entry was refused, unlocated, or simply
    never asked about.
    """

    symbol: str

    statement: StatementKind

    facts: tuple[StatementFact, ...]

    source: PrimarySource

    reading: Provenance

    #: How many places in the document could have opened this statement,
    #: 0 where the reading predates the count. Above one, the section
    #: these figures came from was chosen among contenders and the
    #: provenance claim is an interpretation — reported as uncertain
    #: rather than asserted, which is the honest state until the locator
    #: can resolve statements as the sequence they are.
    located_among: int = 0

    #: Why this reading no longer carries authority, or nothing where it
    #: still does.
    #:
    #: **Authority, never history.** A superseded reading stays in the
    #: file, in the order it was taken, and stays readable: what it
    #: found is still what it found, and deleting it would destroy the
    #: record of what this platform once believed. What it loses is a
    #: vote — the consensus stops counting it, and says so.
    #:
    #: Defaulted, never invented, exactly as `located_among` is: an
    #: entry written before this field existed records nothing, which
    #: reads as *still authoritative* rather than as a claim about an
    #: audit that never ran. That is why this is a field and not a
    #: schema version — a defaulted addition changes neither what a
    #: reading was shown nor what it was asked, so schema-3 entries
    #: load unchanged and unsuperseded ones encode byte-identically.
    #:
    #: Only an offline audit sets it, and only from evidence the source
    #: document itself carries. The reason is stored rather than a flag
    #: so that a reader can see *which* cell disagreed with the filing.
    superseded_because: str | None = None

    #: Which vocabulary each of this reading's concepts was read under.
    #:
    #: **A property of the producer, and never of the reader.** Stamped
    #: once, at acquisition, from the live `CONCEPT_LABELS`; decoded
    #: verbatim thereafter. An old record opened under a new contract
    #: keeps saying what it always said, because saying otherwise would
    #: make the record agree with whatever code happens to be running —
    #: which is the failure BQ16 had to hire an operator's testimony to
    #: work around.
    #:
    #: Empty for everything taken before this field existed, and empty
    #: means *not recorded* rather than *matched today's*: `located_among`
    #: records 0 for the same reason, and BQ16's manifest is the honest
    #: bridge for those records rather than a backfill.
    produced_under: tuple[ConceptContract, ...] = ()

    def produced_contract_for(self, concept: StatementConcept) -> str | None:
        """The vocabulary this reading read one concept under, if recorded."""

        for stamped in self.produced_under:
            if stamped.concept is concept:
                return stamped.fingerprint

        return None

    @property
    def provenance_uncertain(self) -> bool:
        """Whether more than one section could have been this statement."""

        return self.located_among > 1

    @property
    def is_active(self) -> bool:
        """Whether this reading still carries authority."""

        return self.superseded_because is None

    def fact(self, concept: StatementConcept) -> StatementFact | None:
        """This reading's answer for one concept, if it was asked."""

        for fact in self.facts:
            if fact.concept is concept:
                return fact

        return None

    @property
    def located_facts(self) -> tuple[StatementFact, ...]:
        """The concepts this reading located and this platform checked."""

        return tuple(fact for fact in self.facts if fact.is_located)

    def stated_source(self) -> str:
        """The document as an investor would cite it."""

        return self.source.stated()
