"""Carry the four crypto layers that had no wire shape, and interpret nothing.

Asset Quality, Crypto Intelligence, the Intelligence Journal and the
mechanical issuance rule reached the CLI and stopped there. Everything
they say is already worded in the domain — a band's absence, a
question's participation, a claim's epistemic type, a temporal fact's
span — so each adapter here reshapes and formats, and adds no sentence
of its own.

**Every semantic decision is made before this module.** The payload
carries states *and the domain's own sentences* beside them, never the
raw material a client could re-derive a meaning from. The rule
`/committees/{symbol}` already lives by, applied to four more families:
the dashboard presents, and here there is nothing left to calculate.

Three things are deliberately absent. **No aggregate** — nothing sums a
question's points into a headline this layer invented, because the
domain already decided that every crypto asset reads `UNKNOWN` and a
surface computing around that would be overturning S5 in a formatter.
**No favourable/adverse mapping** — `NOT_APPLICABLE` is not a negative
result and `UNKNOWN` is not a zero, so neither is given a sense, a
colour name or a rank here. And **no band `sense`**: `QualityBand`
carries one, nothing on the current corpus produces a band at all, and
shipping a field that has never rendered is shipping an untested
opinion.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.domain.crypto_event import CryptoEvent
from app.domain.crypto_intelligence import CryptoIntelligenceSnapshot
from app.domain.crypto_quality import CryptoAssetQuality, QualityAnswer
from app.domain.crypto_questions import QUESTIONS
from app.domain.intelligence_journal import (
    ObservationSpan,
    TemporalFact,
    shared_maturity,
)
from app.domain.mechanical_issuance import MechanicalIssuance
from app.domain.provenance import Provenance


def _age(moment: datetime | None, source: str = "") -> str | None:
    """The observation's age, worded the way every reading on the page is.

    Routed through `Provenance.stated()` rather than formatted here, so
    a crypto section and an equity one cannot describe the same instant
    two different ways.
    """

    if moment is None:
        return None

    return Provenance(source=source, observed_at=moment).stated()


def _at(moment: datetime | None) -> str | None:
    return moment.isoformat() if moment is not None else None


# ── asset quality ───────────────────────────────────────────────────


def _answer(answer: QualityAnswer) -> dict[str, Any]:
    """One question's participation, with the question in the investor's words.

    `participation` and its `stated` travel together because the states
    are not comparable and a client must never rank them: a question
    that was *shown* carries real evidence nobody scored, and one that
    is *not applicable* carries none because it is the wrong question.
    Printed as two rows of the same table those look like degrees of the
    same thing, so each carries the domain's own sentence saying which
    it is.
    """

    question = QUESTIONS[answer.question]
    rule = answer.rule
    band = answer.band

    return {
        "key": answer.question.value,
        "label": question.label,
        "asks": question.asks,
        "participation": answer.participation.value,
        "participation_stated": answer.participation.stated,
        "stated": answer.stated or None,
        "because": answer.because or None,
        # The rule that produced a verdict, named and versioned so a
        # reader can argue with the threshold rather than the number.
        "rule": f"{rule.name}@{rule.version}" if rule is not None else None,
        "rule_measures": rule.measures if rule is not None else None,
        "band": band.verdict if band is not None else None,
        "band_means": band.means if band is not None else None,
        "source": answer.source,
        # Evidence held and not counted. The content of SHOWN, and the
        # reason a claimed figure can be seen without being scored.
        "shown": list(answer.shown),
    }


def asset_quality_response(quality: CryptoAssetQuality | None) -> dict[str, Any] | None:
    """This asset's quality, including the honest absence of a band.

    `quality` is served as the domain's own token — `UNKNOWN` today for
    every asset — beside `because`, which says why. A client that
    received a null band and no reason would have to invent one, and the
    only sentence available to invent is the wrong one.

    Both coverage ratios travel, never one: `answered / scorable`
    measures this asset's evidence and `scorable / in_scope` measures
    this platform's model, and today the small one is the platform's.
    """

    if quality is None:
        return None

    coverage = quality.coverage

    return {
        "symbol": quality.symbol,
        "quality": quality.quality,
        "because": quality.because,
        "confidence": quality.confidence,
        "earned": quality.earned,
        "available": quality.available,
        "coverage": {
            "applicable": coverage.applicable,
            "undetermined": coverage.undetermined,
            "in_scope": coverage.in_scope,
            "scorable": coverage.scorable,
            "answered": coverage.answered,
            "shown": coverage.shown,
            "unanswerable": coverage.unanswerable,
            "outside": coverage.outside,
            "model_reach": coverage.model_reach,
            "evidence_reach": coverage.evidence_reach,
            "judged_reach": coverage.judged_reach,
        },
        "answers": [_answer(answer) for answer in quality.answers],
    }


# ── what is happening ───────────────────────────────────────────────


def _event(event: CryptoEvent) -> dict[str, Any]:
    """One development, with its accounts kept apart.

    A fact and an interpretation are two different objects here because
    conflating them filed a regulator's suspension as an opinion. They
    travel as two lists, and an interpretation always carries the name
    of whoever made it.
    """

    return {
        "identity": event.identity,
        "family": event.family.value,
        "headline": event.headline,
        "status": event.status.value,
        "entity": event.entity,
        "sources": list(event.sources),
        "is_multi_source": event.is_multi_source,
        "occurred_at": _at(event.occurred_at),
        "published_at": _at(event.published_at),
        "age": _age(event.at),
        "facts": [
            {
                "stated": fact.stated,
                "corroborated_by": list(fact.corroborated_by),
            }
            for fact in event.facts
        ],
        "interpretations": [
            {
                "stated": item.stated,
                "source": item.source,
                "is_causal": item.is_causal,
            }
            for item in event.interpretations
        ],
    }


def intelligence_response(
    snapshot: CryptoIntelligenceSnapshot | None,
) -> dict[str, Any] | None:
    """What changed, what may be driving it, and what to watch.

    Every claim carries its epistemic type — measured, reported,
    attributed, inferred — because a provider's *"inflows are supporting
    BTC"* decomposes into a reported flow, a measured price state and an
    attributed causal link, and a surface that printed the four alike
    would be publishing an opinion as a measurement.

    A driver references its claims by ref and carries none of their
    content, so a client cannot render a driver whose grounds it did not
    also receive.
    """

    if snapshot is None:
        return None

    return {
        "symbol": snapshot.symbol,
        "as_of": _at(snapshot.as_of),
        "thin_because": snapshot.thin_because,
        "claims": [
            {
                "ref": claim.ref,
                "kind": claim.kind.value,
                "claim_type": claim.claim_type.value,
                "claim_type_stated": claim.claim_type.stated,
                "stated": claim.stated,
                "source": claim.source,
                "standing": claim.standing.value,
                "relevance": claim.relevance.value,
                "relevance_stated": claim.relevance.stated,
                "observed_at": _at(claim.observed_at),
                "age": _age(claim.observed_at),
                "does_not_establish": claim.does_not_establish,
            }
            for claim in snapshot.claims
        ],
        "drivers": [
            {
                "stated": driver.stated,
                "direction": driver.direction.value,
                "direction_stated": driver.direction.stated,
                "support": driver.support.value,
                "support_stated": driver.support.stated,
                "matters_because": driver.matters_because,
                "claims": list(driver.claims),
            }
            for driver in snapshot.drivers
        ],
        "events": [_event(event) for event in snapshot.events],
        "narratives": [
            {
                "stated": narrative.stated,
                "source": narrative.source,
                "is_causal": narrative.is_causal,
                "about": narrative.about,
            }
            for narrative in snapshot.narratives
        ],
        "watch_next": [
            {
                "stated": item.stated,
                "measured_by": item.measured_by,
                "because": list(item.because),
                "scheduled_for": _at(item.scheduled_for),
            }
            for item in snapshot.watch_next
        ],
        "foundation": {
            "lines": list(snapshot.foundation.lines),
            "unresolved": list(snapshot.foundation.unresolved),
        },
        "relative_context": list(snapshot.relative_context),
        "conflicting": list(snapshot.conflicting),
        "surfaces_unread": list(snapshot.surfaces_unread),
    }


# ── how long this platform has been looking ─────────────────────────


def _span(span: ObservationSpan) -> dict[str, Any]:
    """The coverage a temporal sentence is allowed to rest on.

    **Three captures across three weeks are not three weeks of
    monitoring**, so the count, the ends and the largest gap all travel
    — and `stated` is the domain's own wording of exactly that. A client
    holding only a first and a last date could word a duration the
    observations do not support, which is the sentence
    `INTELLIGENCE_JOURNAL.md` forbids.
    """

    return {
        "count": span.count,
        "stated": span.stated,
        "first_at": _at(span.first_at),
        "last_at": _at(span.last_at),
        "first_age": _age(span.first_at),
        "last_age": _age(span.last_at),
        "largest_gap_seconds": int(span.largest_gap.total_seconds()),
    }


def _temporal(fact: TemporalFact) -> dict[str, Any]:
    return {
        "key": fact.key,
        "status": fact.status.value,
        "status_stated": fact.status.stated,
        "stated": fact.stated,
        # The reading without its temporal clause. Sent beside `stated`
        # and never instead of it: a client renders this one only where
        # the projection's `shared_maturity` already carries the clause,
        # which is exactly where `carries_span` is true.
        "observed_stated": fact.observed_stated,
        "carries_span": fact.carries_span,
        "nature": fact.nature.value if fact.nature is not None else None,
        "nature_stated": fact.nature.stated if fact.nature is not None else None,
        "previous_value": fact.previous_value,
        "current_value": fact.current_value,
        "unit": fact.unit,
        "run_length": fact.run_length,
        "span": _span(fact.span),
        "entry_ids": list(fact.entry_ids),
    }


def journal_response(
    facts: tuple[TemporalFact, ...],
    captures: int,
) -> dict[str, Any] | None:
    """The deterministic reading of the append-only record.

    Leads with coverage rather than with a finding, because how often
    this platform looked decides what any of the findings beneath it can
    responsibly claim. Null where nothing was ever captured — an empty
    journal rendered as a table of zero rows reads as stability.

    `shared_maturity` is that lead sentence where every finding shares
    one: the domain decides whether they do, and null means they do not
    and each finding carries its own.
    """

    if not captures:
        return None

    shared = shared_maturity(facts)

    return {
        "captures": captures,
        "shared_maturity": (
            None
            if shared is None
            else {
                "status": shared.status.value,
                "status_stated": shared.status_stated,
                "span_stated": shared.span_stated,
                "count": shared.count,
                "stated": shared.stated,
            }
        ),
        "facts": [_temporal(fact) for fact in facts],
    }


# ── what is still to be issued, and under what rule ─────────────────


def issuance_response(rule: MechanicalIssuance | None) -> dict[str, Any] | None:
    """The issuance rule as read, and what it implies under itself.

    **Never a forecast.** `path` is arithmetic under the currently
    observed policy and `mutability` says who could change that policy,
    so the two travel together and a client cannot render a path without
    the sentence that qualifies it.

    Null for an allocation-release asset rather than empty: a token
    whose supply reaches the market by unlock has no mechanical rule,
    and an empty rule table would read as one that could not be found.
    """

    if rule is None:
        return None

    state = rule.state

    return {
        "symbol": rule.symbol,
        "mechanism": rule.mechanism.value,
        "mechanism_stated": rule.mechanism.stated,
        "mechanism_described": rule.mechanism.described,
        "formula": rule.formula,
        "standing": rule.standing.value,
        "authority": rule.authority.value,
        "source": rule.source,
        "because": rule.because,
        "caveats": list(rule.caveats),
        "is_projectable": rule.is_projectable,
        "parameters_are_all_read": rule.parameters_are_all_read,
        "mutability": rule.mutability.value,
        "mutability_stated": rule.mutability.stated,
        "mutability_because": rule.mutability.because,
        "state": {
            "position": state.position,
            "observed_at": _at(state.observed_at),
            "age": _age(state.observed_at),
            "unit": state.unit,
            "emitted": state.emitted,
            # Carried because a figure this platform computed and one a
            # source published are different evidence, and printed alike
            # the weaker borrows the stronger's authority.
            "emitted_is_derived": state.emitted_is_derived,
            "remaining": state.remaining,
            "current_rate": state.current_rate,
        },
        "parameters": [
            {
                "name": parameter.name,
                "value": parameter.value,
                "unit": parameter.unit,
                "means": parameter.means,
                "read_from": parameter.read_from,
            }
            for parameter in rule.parameters
        ],
        "path": [
            {
                "horizon": step.horizon,
                "issuance": step.issuance,
                "unit": step.unit,
                "share_of_emitted": step.share_of_emitted,
                "rule_version": step.rule_version,
            }
            for step in rule.path
        ],
    }
