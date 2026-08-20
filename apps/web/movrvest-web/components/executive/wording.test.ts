import { describe, expect, it } from "vitest";

import {
  EXECUTION_HEADLINE,
  INCOMPLETE_HISTORY,
  READABLE_HEADLINE,
} from "./LatestCioReview";
import { FAILURE_MEANING } from "../../app/page";

/**
 * Two claims the page must never make.
 *
 * With an incomplete history the newest decoded record is only the
 * newest *readable* record — an unreadable line may be newer — so no
 * headline may call it "the last review". And an unreadable response is
 * not an unreachable backend: calling it one would be a claim about the
 * network made out of a parsing problem.
 */

describe("an incomplete history never claims the latest attempt", () => {
  it("words every state as readable rather than last", () => {
    for (const [state, headline] of Object.entries(READABLE_HEADLINE)) {
      expect(headline.toLowerCase(), state).not.toContain("the last review");

      if (state !== "none_recorded") {
        expect(headline.toLowerCase(), state).toContain("latest readable");
      }
    }
  });

  it("differs from the complete-history wording in every state", () => {
    for (const state of Object.keys(READABLE_HEADLINE)) {
      const key = state as keyof typeof READABLE_HEADLINE;

      expect(READABLE_HEADLINE[key]).not.toBe(EXECUTION_HEADLINE[key]);
    }
  });

  it("says outright that a newer attempt may exist", () => {
    expect(INCOMPLETE_HISTORY).toContain("not necessarily the latest one");
    expect(INCOMPLETE_HISTORY.toLowerCase()).toContain("newer review may exist");
  });
});

describe("three failures are three different sentences", () => {
  it("never calls an unreadable response an unreachable backend", () => {
    expect(FAILURE_MEANING.invalid_contract.toLowerCase()).not.toContain(
      "could not reach",
    );
    expect(FAILURE_MEANING.invalid_contract).toContain("could not read");
    expect(FAILURE_MEANING.http_error.toLowerCase()).not.toContain(
      "could not reach",
    );
    expect(FAILURE_MEANING.unreachable.toLowerCase()).toContain(
      "could not reach",
    );
  });

  it("gives each failure its own wording", () => {
    const said = Object.values(FAILURE_MEANING);

    expect(new Set(said).size).toBe(said.length);
  });
});
