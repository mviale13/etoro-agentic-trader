"use client";

import { useState } from "react";

import { AnalysisResultsStep } from "./steps/AnalysisResultsStep";
import { StepComplete } from "./steps/CompleteStep";
import { StepGoals } from "./steps/GoalsStep";
import { StepHypotheses } from "./steps/HypothesesStep";
import { StepPhilosophy } from "./steps/PhilosophyStep";
import { StepPolicy } from "./steps/PolicyStep";
import { StepPortfolioAnalysis } from "./steps/PortfolioAnalysisStep";
import { StepWelcome } from "./steps/WelcomeStep";

const STEPS = [
  "welcome",
  "portfolio-analysis",
  "analysis-results",
  "hypotheses",
  "goals",
  "philosophy",
  "policy",
  "complete",
] as const;

type OnboardingStep = (typeof STEPS)[number];

export function InvestorOnboarding() {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const currentStep: OnboardingStep = STEPS[currentStepIndex];

  const goToNextStep = () => {
    setCurrentStepIndex((index) =>
      Math.min(index + 1, STEPS.length - 1),
    );
  };

  const goToPreviousStep = () => {
    setCurrentStepIndex((index) => Math.max(index - 1, 0));
  };

  switch (currentStep) {
    case "welcome":
      return <StepWelcome onContinue={goToNextStep} />;

    case "portfolio-analysis":
      return <StepPortfolioAnalysis onContinue={goToNextStep} />;

    case "analysis-results":
      return (
        <AnalysisResultsStep
          onBack={goToPreviousStep}
          onContinue={goToNextStep}
        />
      );

    case "hypotheses":
      return (
        <StepHypotheses
          onBack={goToPreviousStep}
          onContinue={goToNextStep}
        />
      );

    case "goals":
      return (
        <StepGoals
          onBack={goToPreviousStep}
          onContinue={goToNextStep}
        />
      );

    case "philosophy":
      return (
        <StepPhilosophy
          onBack={goToPreviousStep}
          onContinue={goToNextStep}
        />
      );

    case "policy":
      return (
        <StepPolicy
          onBack={goToPreviousStep}
          onContinue={goToNextStep}
        />
      );

    case "complete":
      return <StepComplete />;

    default:
      return <StepWelcome onContinue={goToNextStep} />;
  }
}
