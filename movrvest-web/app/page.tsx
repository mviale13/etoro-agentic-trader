import { BrainCard } from "@/components/dashboard/BrainCard";
import { ChangesCard } from "@/components/dashboard/ChangesCard";
import { CommitteeWeightsCard } from "@/components/dashboard/CommitteeWeightsCard";
import { DoctorCard } from "@/components/dashboard/DoctorCard";
import { ExplainCard } from "@/components/dashboard/ExplainCard";
import { Header } from "@/components/dashboard/Header";
import { InvestorDNACard } from "@/components/dashboard/InvestorDNACard";
import { NextActionCard } from "@/components/dashboard/NextActionCard";
import { ObservationCard } from "@/components/dashboard/ObservationCard";
import { PortfolioCard } from "@/components/dashboard/PortfolioCard";
import { ReflectionCard } from "@/components/dashboard/ReflectionCard";
import { TopOpportunitiesCard } from "@/components/dashboard/TopOpportunitiesCard";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

import { getToday } from "@/lib/api";
import { getBrain } from "@/lib/brain-api";
import { getCommitteeWeights } from "@/lib/committee-weights-api";
import { getDoctor } from "@/lib/doctor-api";
import { getExplanation } from "@/lib/explanation-api";
import { getOpportunities } from "@/lib/opportunities-api";
import { getReflection } from "@/lib/reflection-api";

export default async function Home() {
  const today = await getToday();
  const doctor = await getDoctor();
  const explanation = await getExplanation();
  const reflection = await getReflection();
  const opportunities = await getOpportunities();
  const committeeWeights = await getCommitteeWeights();
  const brain = await getBrain();

  const opportunitiesArePrimary =
    brain.focus === "opportunities";

  return (
    <DashboardLayout>
      <Header greeting={today.greeting} />

      <BrainCard brain={brain} />

      {opportunitiesArePrimary && (
        <TopOpportunitiesCard
          opportunities={opportunities}
        />
      )}

      {doctor && (
        <DoctorCard
          health={doctor.health}
          diagnosis={doctor.diagnosis}
          prescriptions={doctor.prescriptions}
          projectedHealth={doctor.projected_health}
        />
      )}

      <ExplainCard
        recommendation={explanation.recommendation}
        confidence={explanation.confidence}
        reasons={explanation.reasons}
      />

      <section className="grid gap-6 md:grid-cols-2">
        <ChangesCard changes={today.changes} />

        {!opportunitiesArePrimary && (
          <TopOpportunitiesCard
            opportunities={opportunities}
          />
        )}

        <InvestorDNACard
          dna={{
            understanding: brain.investor_dna.confidence,
            message:
              brain.investor_dna.message ??
              "MOVRvest is still learning your investment behaviour.",
          }}
        />

        <CommitteeWeightsCard
          data={committeeWeights}
        />

        <PortfolioCard
          portfolio={{
            total_value: brain.portfolio.total_value,
            total_value_eur:
              brain.portfolio.total_value_eur,
            positions: brain.portfolio.positions,
            allocation: {
              cash: brain.portfolio.cash_allocation,
              stocks: 0,
              etfs: 0,
              crypto: 0,
              unclassified: 0,
            },
            risk_flags: [],
          }}
        />

        <ObservationCard
          observation={{
            title: brain.observation.title,
            message: brain.observation.message,
            category: "general",
          }}
        />

        <NextActionCard
          action={today.next_action}
        />

        <ReflectionCard
          reflection={reflection}
        />
      </section>
    </DashboardLayout>
  );
}
