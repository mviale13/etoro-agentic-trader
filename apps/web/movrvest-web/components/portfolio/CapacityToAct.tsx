import { Banknote, ChartPie, Coins, Gauge } from "lucide-react";

import { StatusPill } from "@/components/ui/StatusPill";
import type { PortfolioCapacity } from "@/lib/api/portfolio";

const usdFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

type CapacityRowProps = {
  label: string;
  reading: string | null;
  detail: string;
  breached?: boolean;
  icon: typeof Banknote;
};

/**
 * One capacity term: what was measured, in the Brain's own figures.
 *
 * A null reading renders as "Not measured" — the reason arrives in the
 * assessment's `unmeasured` list and is printed under the rows, so an
 * absence is always accompanied by why it is absent.
 */
function CapacityRow({
  label,
  reading,
  detail,
  breached = false,
  icon: Icon,
}: CapacityRowProps) {
  return (
    <div className="flex flex-col gap-2 border-b border-slate-100 py-4 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <Icon aria-hidden="true" className="h-5 w-5 shrink-0 text-slate-500" />

        <div>
          <span className="font-medium text-slate-900">{label}</span>

          <p className="text-sm leading-6 text-slate-500">{detail}</p>
        </div>
      </div>

      {reading === null ? (
        <span className="shrink-0 text-sm font-medium text-slate-400">
          Not measured
        </span>
      ) : (
        <span
          className={`shrink-0 text-sm font-semibold ${
            breached ? "text-red-700" : "text-slate-900"
          }`}
        >
          {reading}
        </span>
      )}
    </div>
  );
}

function points(value: number): string {
  return `${Math.abs(value).toFixed(1)} pts`;
}

export function CapacityToAct({
  capacity,
}: {
  capacity: PortfolioCapacity | null;
}) {
  if (capacity === null) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <h2 className="text-xl font-semibold tracking-tight text-slate-950">
            Capacity to act
          </h2>

          <StatusPill status="partial" label="Capacity unavailable" />
        </div>

        <p className="mt-4 leading-7 text-slate-600">
          The Brain did not report a capacity assessment with this snapshot,
          so the room this account has to act is unknown — it is not zero.
        </p>
      </section>
    );
  }

  const overLimit =
    capacity.singlePositionHeadroomPct !== null &&
    capacity.singlePositionHeadroomPct < 0;

  // Wordings only. Every figure below arrives measured from the backend;
  // this component decides phrasing, never values.
  const fundingReading =
    capacity.fundingRoomPct === null
      ? null
      : capacity.fundingRoomUsd === null
        ? points(capacity.fundingRoomPct)
        : `${usdFormatter.format(capacity.fundingRoomUsd)} · ${points(
            capacity.fundingRoomPct,
          )}`;

  const fundingDetail =
    capacity.cashTargetPct === null
      ? "Cash the policy does not want held as cash"
      : `Cash is ${capacity.cashActualPct.toFixed(1)}% of the account against a ${capacity.cashTargetPct.toFixed(0)}% policy target`;

  const concentrationReading =
    capacity.singlePositionHeadroomPct === null
      ? null
      : overLimit
        ? `${points(capacity.singlePositionHeadroomPct)} over the limit`
        : `${points(capacity.singlePositionHeadroomPct)} of room`;

  const concentrationDetail =
    capacity.singlePositionLimitPct === null
      ? "The policy sets no single-position limit"
      : capacity.largestPosition === null ||
          capacity.largestPositionPct === null
        ? `No holdings yet — the whole ${capacity.singlePositionLimitPct.toFixed(0)}% single-position limit is open`
        : `${capacity.largestPosition} holds ${capacity.largestPositionPct.toFixed(1)}% of the account against a ${capacity.singlePositionLimitPct.toFixed(0)}% limit`;

  const cryptoReading =
    capacity.cryptoHeadroomPct === null
      ? null
      : capacity.cryptoHeadroomPct < 0
        ? `${points(capacity.cryptoHeadroomPct)} over the ceiling`
        : `${points(capacity.cryptoHeadroomPct)} of room`;

  const cryptoDetail =
    capacity.cryptoLimitPct === null
      ? "The policy sets no crypto ceiling"
      : capacity.cryptoActualPct === null
        ? `The policy caps crypto at ${capacity.cryptoLimitPct.toFixed(0)}% of the account`
        : `Crypto is ${capacity.cryptoActualPct.toFixed(1)}% of the account against a ${capacity.cryptoLimitPct.toFixed(0)}% ceiling`;

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
            <Gauge aria-hidden="true" className="h-5 w-5" />
          </div>

          <div>
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">
              Capacity to act
            </h2>

            <p className="mt-1 text-sm leading-6 text-slate-500">
              Room measured against the limits the investor policy states.
            </p>
          </div>
        </div>

        <StatusPill
          status={capacity.unmeasured.length === 0 ? "live" : "partial"}
          label={
            capacity.unmeasured.length === 0
              ? "Fully measured"
              : `${capacity.unmeasured.length} unmeasured`
          }
        />
      </div>

      <div className="mt-6">
        <CapacityRow
          detail={fundingDetail}
          icon={Banknote}
          label="Funding room"
          reading={fundingReading}
        />

        <CapacityRow
          breached={overLimit}
          detail={concentrationDetail}
          icon={ChartPie}
          label="Single-position headroom"
          reading={concentrationReading}
        />

        <CapacityRow
          detail={cryptoDetail}
          icon={Coins}
          label="Crypto ceiling"
          reading={cryptoReading}
        />
      </div>

      {capacity.unmeasured.length > 0 ? (
        <ul className="mt-4 space-y-1 text-sm text-slate-500">
          {capacity.unmeasured.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
