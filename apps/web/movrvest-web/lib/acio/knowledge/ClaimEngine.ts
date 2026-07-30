import { Claim } from "./types";

export class ClaimEngine {
  static create(claim: Claim): Claim {
    return claim;
  }

  static confirm(claim: Claim): Claim {
    return {
      ...claim,
      status: "confirmed",
      updatedAt: new Date().toISOString(),
    };
  }

  static reject(claim: Claim): Claim {
    return {
      ...claim,
      status: "rejected",
      updatedAt: new Date().toISOString(),
    };
  }

  static supersede(
    previous: Claim,
    replacement: Claim,
  ): Claim {
    previous.status = "superseded";

    return replacement;
  }
}
