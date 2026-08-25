"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import {
  InvestorStrategy,
  updateStrategy,
} from "@/lib/strategy-api";

type Props = {
  initialStrategy: InvestorStrategy;
};

const inputClass =
  "mt-2 w-full rounded-lg border border-slate-700 " +
  "bg-slate-900 px-3 py-2 text-slate-100";

function parseOptionalNumber(
  value: string,
): number | null {
  if (value.trim() === "") {
    return null;
  }

  return Number(value);
}

function parseList(
  value: string,
): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function InvestmentPolicyForm({
  initialStrategy,
}: Props) {
  const router = useRouter();

  const [strategy, setStrategy] =
    useState<InvestorStrategy>(
      initialStrategy,
    );

  const [saving, setSaving] =
    useState(false);

  const [message, setMessage] =
    useState("");

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setSaving(true);
    setMessage("");

    try {
      await updateStrategy({
        ...strategy,
        status: "draft",
      });

      setMessage(
        "Investment Policy saved.",
      );

      router.refresh();
    } catch {
      setMessage(
        "Unable to save the Investment Policy.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-8"
    >
      <section className="rounded-xl border border-slate-800 p-6">
        <h2 className="text-xl font-semibold">
          Investor profile
        </h2>

        <div className="mt-4 grid gap-5 md:grid-cols-2 2xl:grid-cols-3">
          <label>
            Name
            <input
              className={inputClass}
              value={strategy.profile.name}
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  profile: {
                    ...strategy.profile,
                    name: event.target.value,
                  },
                })
              }
            />
          </label>

          <label>
            Base currency
            <select
              className={inputClass}
              value={strategy.profile.base_currency}
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  profile: {
                    ...strategy.profile,
                    base_currency: event.target.value,
                  },
                })
              }
            >
              <option value="EUR">EUR</option>
              <option value="USD">USD</option>
              <option value="GBP">GBP</option>
              <option value="CHF">CHF</option>
            </select>
          </label>

          <label>
            Investor type
            <select
              className={inputClass}
              value={
                strategy.investment_preferences
                  .investor_type ?? ""
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  investment_preferences: {
                    ...strategy.investment_preferences,
                    investor_type:
                      event.target.value,
                  },
                })
              }
            >
              <option value="">
                Select investor type
              </option>
              <option value="long_term">
                Long-term investor
              </option>
              <option value="swing">
                Swing trader
              </option>
              <option value="day_trader">
                Day trader
              </option>
              <option value="etf">
                ETF investor
              </option>
              <option value="dividend">
                Dividend investor
              </option>
              <option value="crypto">
                Crypto investor
              </option>
              <option value="custom">
                Custom
              </option>
            </select>
          </label>
        </div>
      </section>

      <section className="rounded-xl border border-slate-800 p-6">
        <h2 className="text-xl font-semibold">
          Objectives
        </h2>

        <div className="mt-4 grid gap-5 md:grid-cols-2 2xl:grid-cols-3">
          <label className="md:col-span-2">
            Primary goal
            <textarea
              className={inputClass}
              rows={3}
              value={
                strategy.objectives.primary_goal
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  objectives: {
                    ...strategy.objectives,
                    primary_goal:
                      event.target.value,
                  },
                })
              }
              placeholder="Example: Grow capital while limiting large drawdowns."
            />
          </label>

          <label>
            Time horizon in years
            <input
              className={inputClass}
              type="number"
              min="0"
              step="1"
              value={
                strategy.objectives
                  .time_horizon_years ?? ""
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  objectives: {
                    ...strategy.objectives,
                    time_horizon_years:
                      parseOptionalNumber(
                        event.target.value,
                      ),
                  },
                })
              }
            />
          </label>

          <label>
            Target annual return %
            <input
              className={inputClass}
              type="number"
              min="0"
              step="0.1"
              value={
                strategy.objectives
                  .target_annual_return_pct ?? ""
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  objectives: {
                    ...strategy.objectives,
                    target_annual_return_pct:
                      parseOptionalNumber(
                        event.target.value,
                      ),
                  },
                })
              }
            />
          </label>

          <label>
            Maximum acceptable drawdown %
            <input
              className={inputClass}
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={
                strategy.objectives
                  .maximum_acceptable_drawdown_pct ??
                ""
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  objectives: {
                    ...strategy.objectives,
                    maximum_acceptable_drawdown_pct:
                      parseOptionalNumber(
                        event.target.value,
                      ),
                  },
                })
              }
            />
          </label>
        </div>
      </section>

      <section className="rounded-xl border border-slate-800 p-6">
        <h2 className="text-xl font-semibold">
          Portfolio limits
        </h2>

        <div className="mt-4 grid gap-5 md:grid-cols-2 2xl:grid-cols-3">
          <label>
            Target cash allocation %
            <input
              className={inputClass}
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={
                strategy.portfolio_policy
                  .target_cash_pct ?? ""
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  portfolio_policy: {
                    ...strategy.portfolio_policy,
                    target_cash_pct:
                      parseOptionalNumber(
                        event.target.value,
                      ),
                  },
                })
              }
            />
          </label>

          <label>
            Minimum cash allocation %
            <input
              className={inputClass}
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={
                strategy.portfolio_policy
                  .minimum_cash_pct ?? ""
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  portfolio_policy: {
                    ...strategy.portfolio_policy,
                    minimum_cash_pct:
                      parseOptionalNumber(
                        event.target.value,
                      ),
                  },
                })
              }
            />
          </label>

          <label>
            Maximum single position %
            <input
              className={inputClass}
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={
                strategy.portfolio_policy
                  .maximum_single_position_pct ??
                ""
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  portfolio_policy: {
                    ...strategy.portfolio_policy,
                    maximum_single_position_pct:
                      parseOptionalNumber(
                        event.target.value,
                      ),
                  },
                })
              }
            />
          </label>

          <label>
            Maximum crypto allocation %
            <input
              className={inputClass}
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={
                strategy.portfolio_policy
                  .maximum_crypto_pct ?? ""
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  portfolio_policy: {
                    ...strategy.portfolio_policy,
                    maximum_crypto_pct:
                      parseOptionalNumber(
                        event.target.value,
                      ),
                  },
                })
              }
            />
          </label>
        </div>
      </section>

      <section className="rounded-xl border border-slate-800 p-6">
        <h2 className="text-xl font-semibold">
          Investment preferences
        </h2>

        <div className="mt-4 space-y-5">
          <label className="block">
            Investment styles
            <input
              className={inputClass}
              value={
                strategy.investment_preferences
                  .style.join(", ")
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  investment_preferences: {
                    ...strategy.investment_preferences,
                    style: parseList(
                      event.target.value,
                    ),
                  },
                })
              }
              placeholder="growth, value, momentum, dividend"
            />
          </label>

          <label className="block">
            Preferred assets
            <input
              className={inputClass}
              value={
                strategy.investment_preferences
                  .preferred_assets.join(", ")
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  investment_preferences: {
                    ...strategy.investment_preferences,
                    preferred_assets: parseList(
                      event.target.value,
                    ),
                  },
                })
              }
              placeholder="stocks, ETFs, crypto"
            />
          </label>

          <label className="block">
            Excluded assets
            <input
              className={inputClass}
              value={
                strategy.investment_preferences
                  .excluded_assets.join(", ")
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  investment_preferences: {
                    ...strategy.investment_preferences,
                    excluded_assets: parseList(
                      event.target.value,
                    ),
                  },
                })
              }
              placeholder="tobacco, weapons, leveraged ETFs"
            />
          </label>

          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={
                  strategy.investment_preferences
                    .allow_crypto
                }
                onChange={(event) =>
                  setStrategy({
                    ...strategy,
                    investment_preferences: {
                      ...strategy.investment_preferences,
                      allow_crypto:
                        event.target.checked,
                    },
                  })
                }
              />
              Allow crypto
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={
                  strategy.investment_preferences
                    .allow_leverage
                }
                onChange={(event) =>
                  setStrategy({
                    ...strategy,
                    investment_preferences: {
                      ...strategy.investment_preferences,
                      allow_leverage:
                        event.target.checked,
                    },
                  })
                }
              />
              Allow leverage
            </label>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-800 p-6">
        <h2 className="text-xl font-semibold">
          Decision rules
        </h2>

        <div className="mt-4 space-y-5">
          <label className="block">
            Minimum committee confidence to buy %
            <input
              className={inputClass}
              type="number"
              min="0"
              max="100"
              step="1"
              value={
                strategy.decision_rules
                  .minimum_committee_confidence_to_buy ??
                ""
              }
              onChange={(event) =>
                setStrategy({
                  ...strategy,
                  decision_rules: {
                    ...strategy.decision_rules,
                    minimum_committee_confidence_to_buy:
                      parseOptionalNumber(
                        event.target.value,
                      ),
                  },
                })
              }
            />
          </label>

          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={
                  strategy.decision_rules
                    .require_human_approval
                }
                onChange={(event) =>
                  setStrategy({
                    ...strategy,
                    decision_rules: {
                      ...strategy.decision_rules,
                      require_human_approval:
                        event.target.checked,
                    },
                  })
                }
              />
              Require human approval
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={
                  strategy.decision_rules
                    .automatic_trading_enabled
                }
                onChange={(event) =>
                  setStrategy({
                    ...strategy,
                    decision_rules: {
                      ...strategy.decision_rules,
                      automatic_trading_enabled:
                        event.target.checked,
                    },
                  })
                }
              />
              Enable automatic trading
            </label>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-800 p-6">
        <h2 className="text-xl font-semibold">
          Notes
        </h2>

        <textarea
          className={inputClass}
          rows={5}
          value={strategy.notes.join("\n")}
          onChange={(event) =>
            setStrategy({
              ...strategy,
              notes: event.target.value
                .split("\n")
                .map((item) => item.trim())
                .filter(Boolean),
            })
          }
          placeholder="One note per line"
        />
      </section>

      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"
        >
          {saving
            ? "Saving..."
            : "Save Investment Policy"}
        </button>

        {message && (
          <p className="text-sm text-slate-300">
            {message}
          </p>
        )}
      </div>
    </form>
  );
}
