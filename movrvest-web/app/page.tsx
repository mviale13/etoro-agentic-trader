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

export default async function Home() {
  const today = await getToday();
  const doctor = await getDoctor();
  const explanation = await getExplanation();
  const opportunities = await getOpportunities();

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

          <PortfolioHealthCard
            score={today.health.score}
            summary={today.summary}
          />

          <NextActionCard action={today.next_action} />
        </section>
    </DashboardLayout>
  );
}