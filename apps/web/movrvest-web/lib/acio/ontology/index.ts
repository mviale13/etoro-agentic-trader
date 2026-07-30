export {
  PortfolioEvidenceKinds,
  type PortfolioEvidenceKind,
} from "./portfolio";

export {
  MarketEvidenceKinds,
  type MarketEvidenceKind,
} from "./market";

export {
  CompanyEvidenceKinds,
  type CompanyEvidenceKind,
} from "./company";

export {
  MacroEvidenceKinds,
  type MacroEvidenceKind,
} from "./macro";

export {
  InvestorEvidenceKinds,
  type InvestorEvidenceKind,
} from "./investor";

import type { PortfolioEvidenceKind } from "./portfolio";
import type { MarketEvidenceKind } from "./market";
import type { CompanyEvidenceKind } from "./company";
import type { MacroEvidenceKind } from "./macro";
import type { InvestorEvidenceKind } from "./investor";

export type EvidenceKind =
  | PortfolioEvidenceKind
  | MarketEvidenceKind
  | CompanyEvidenceKind
  | MacroEvidenceKind
  | InvestorEvidenceKind;
