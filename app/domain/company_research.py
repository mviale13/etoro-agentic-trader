"""What the analysts a security's playbook asked for concluded."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.domain.company_knowledge import CompanyKnowledge
from app.domain.playbook import InvestmentPlaybook
from app.domain.research_plan import AnalystKey


@dataclass(frozen=True, slots=True)
class CompanyResearch:
    """Complete fundamental research produced for a security.

    The aggregate root of the company research domain: the playbook the
    security was read with, and the opinion of every analyst that playbook
    asked for.

    It once held exactly four opinions, one per analyst, as named fields —
    which made it impossible to express a security read any other way. A
    bank without a cash-flow analyst and a token with no analysts at all
    could not be represented, so every security was analysed identically
    whatever the playbook said. The opinions are keyed now, and an analyst
    the playbook declined is absent here and explained there.
    """

    playbook: InvestmentPlaybook

    opinions: Mapping[AnalystKey, Any] = field(default_factory=dict)

    #: What this company structurally is, read from its own published
    #: account of itself. None where no authoritative source could be
    #: reached — which `knowledge_state` distinguishes from a source that
    #: was read and failed validation.
    knowledge: CompanyKnowledge | None = None

    #: How that knowledge was obtained, or why it was not. Carried so a
    #: surface can report analysis coverage honestly rather than showing
    #: a company with no segments beside one nobody looked for.
    knowledge_state: str | None = None

    def opinion(self, key: AnalystKey) -> Any | None:
        """One analyst's verdict, or nothing where it was not asked."""

        return self.opinions.get(key)

    @property
    def was_analysed(self) -> bool:
        """Whether any analyst was asked about this security at all."""

        return bool(self.opinions)
