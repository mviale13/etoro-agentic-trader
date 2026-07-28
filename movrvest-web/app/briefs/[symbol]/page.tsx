import { ExecutiveBrief } from "@/components/brief/ExecutiveBrief";
import { microsoftExecutiveBrief } from "@/mocks/executive-brief";

export default function BriefPage() {
  return <ExecutiveBrief brief={microsoftExecutiveBrief} />;
}
