import { getToday } from "@/lib/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/dashboard/Header";
import { OpportunityCard } from "@/components/dashboard/OpportunityCard";
import { PortfolioHealthCard } from "@/components/dashboard/PortfolioHealthCard";
import { ChangesCard } from "@/components/dashboard/ChangesCard";
import { NextActionCard } from "@/components/dashboard/NextActionCard";
import { DoctorCard } from "@/components/dashboard/DoctorCard";
import { getDoctor } from "@/lib/doctor-api";

export default async function Home() {
  const today = await getToday();
  const doctor = await getDoctor();

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
        <section className="grid gap-6 md:grid-cols-2">
          <ChangesCard changes={today.changes} />

          <OpportunityCard
            symbol={today.recommendation.symbol}
            action={today.recommendation.action}
            confidence={today.recommendation.confidence}
          />

          <PortfolioHealthCard
            score={today.health.score}
            summary={today.summary}
          />

          <NextActionCard action={today.next_action} />
        </section>
    </DashboardLayout>
  );
}