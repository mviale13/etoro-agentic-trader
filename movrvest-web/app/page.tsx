import { getToday } from "@/lib/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/dashboard/Header";
import { PortfolioHealthCard } from "@/components/dashboard/PortfolioHealthCard";
import { ChangesCard } from "@/components/dashboard/ChangesCard";
import { NextActionCard } from "@/components/dashboard/NextActionCard";
import { DoctorCard } from "@/components/dashboard/DoctorCard";
import { getDoctor } from "@/lib/doctor-api";
import { ExplainCard } from "@/components/dashboard/ExplainCard";
import { getExplanation } from "@/lib/explanation-api";
import { TopOpportunitiesCard } from "@/components/dashboard/TopOpportunitiesCard";
import { getOpportunities } from "@/lib/opportunities-api";
import { ReflectionCard } from "@/components/dashboard/ReflectionCard";
import { getReflection } from "@/lib/reflection-api";
import { getPortfolioHealth } from "@/lib/portfolio-health-api";
import { InvestorDNACard } from "@/components/dashboard/InvestorDNACard";
import { getInvestorDNA } from "@/lib/investor-dna-api";
import { getPortfolio } from "@/lib/portfolio-api";
import { PortfolioCard } from "@/components/dashboard/PortfolioCard";
import { getObservation } from "@/lib/observation-api";
import { ObservationCard } from "@/components/dashboard/ObservationCard";

export default async function Home() {
  const today = await getToday();
  const doctor = await getDoctor();
  const explanation = await getExplanation();
  const portfolio = await getPortfolio();
  const portfolioHealth = await getPortfolioHealth();
  const reflection = await getReflection();
  const opportunities = await getOpportunities();
  const dna = await getInvestorDNA();
  const observation = await getObservation().catch(() => null);

  return (
    <DashboardLayout>
      <Header greeting={today.greeting} />
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

          <TopOpportunitiesCard opportunities={opportunities} />
          <InvestorDNACard dna={dna} />
          {
            portfolio ? (
              <PortfolioCard portfolio={portfolio} />
            ) : (
              <PortfolioHealthCard health={portfolioHealth} />
            )
          }
          {observation && (
            <ObservationCard observation={observation} />
          )}
          <NextActionCard action={today.next_action} />
          <ReflectionCard reflection={reflection} />
        </section>
    </DashboardLayout>
  );
}