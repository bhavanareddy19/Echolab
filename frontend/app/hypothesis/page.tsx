'use client';

import { Dashboard } from '@/components/Dashboard';
import HypothesisContainer from '@/components/UI/HypothesisContainer';
import Breadcrumb from '@/components/UI/Breadcrumb';
import { useState } from 'react';
import type { Hypothesis } from '@/types';

export default function Hypothesis() {
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([
    {
      checked: false,
      editMode: {
        if: false,
        then: false,
        variantA: false,
        variantB: false,
      },
      current: {
        if: 'We optimize checkout page load time by implementing lazy loading for non-critical elements',
        then: 'Conversion rate and time-to-completion will improve because users are abandoning due to slow page performance',
        variantA: 'Current static FAQ link',
        variantB: 'New interactive FAQ with search',
      },
      temp: {
        if: 'We optimize checkout page load time by implementing lazy loading for non-critical elements',
        then: 'Conversion rate and time-to-completion will improve because users are abandoning due to slow page performance',
        variantA: 'Current static FAQ link',
        variantB: 'New interactive FAQ with search',
      },
    },
    {
      checked: false,
      editMode: {
        if: false,
        then: false,
        variantA: false,
        variantB: false,
      },
      current: {
        if: 'We simplify the onboarding process by reducing the number of required steps from 8 to 4',
        then: 'User completion rate will increase and support tickets will decrease because the current process is too complex',
        variantA: 'Current 8-step onboarding flow',
        variantB: 'Streamlined 4-step onboarding with progress indicator',
      },
      temp: {
        if: 'We simplify the onboarding process by reducing the number of required steps from 8 to 4',
        then: 'User completion rate will increase and support tickets will decrease because the current process is too complex',
        variantA: 'Current 8-step onboarding flow',
        variantB: 'Streamlined 4-step onboarding with progress indicator',
      },
    },
    {
      checked: false,
      editMode: {
        if: false,
        then: false,
        variantA: false,
        variantB: false,
      },
      current: {
        if: 'We add contextual help tooltips throughout the application interface',
        then: 'User satisfaction scores will improve and feature adoption will increase because users struggle with understanding advanced features',
        variantA: 'Current help documentation in separate section',
        variantB:
          'Contextual tooltips that appear on hover with relevant guidance',
      },
      temp: {
        if: 'We add contextual help tooltips throughout the application interface',
        then: 'User satisfaction scores will improve and feature adoption will increase because users struggle with understanding advanced features',
        variantA: 'Current help documentation in separate section',
        variantB:
          'Contextual tooltips that appear on hover with relevant guidance',
      },
    },
  ]);

  const handleHypothesisChange = (
    index: number,
    updatedHypothesis: Hypothesis
  ) => {
    const newHypotheses = [...hypotheses];
    newHypotheses[index] = updatedHypothesis;
    setHypotheses(newHypotheses);
  };

  const sampleData = [
    {
      title: 'Hypothesis 1',
      primaryMetric: 'conversion-rate',
      secondaryMetric: 'time-to-completion',
      impactPercentage: 92,
      impactLevel: 'High' as const,
      inspiration:
        'Appcues blog — "Checklists provide an explicit list of tasks for the user to complete."',
    },
    {
      title: 'Hypothesis 2',
      primaryMetric: 'completion-rate',
      secondaryMetric: 'support-tickets',
      impactPercentage: 64,
      impactLevel: 'Medium' as const,
      inspiration:
        'Nielsen Norman Group — "Reducing cognitive load improves user experience and completion rates."',
    },
    {
      title: 'Hypothesis 3',
      primaryMetric: 'user-satisfaction',
      secondaryMetric: 'feature-adoption',
      impactPercentage: 35,
      impactLevel: 'Low' as const,
      inspiration:
        'UX Planet — "Contextual help reduces user frustration and increases feature discovery."',
    },
  ];

  return (
    <Dashboard>
      <div className="flex flex-col gap-5">
        <Breadcrumb
          items={[
            { label: 'Dashboard', href: '/' },
            { label: 'Pain points details', href: '/painpoints' },
            { label: 'Hypothesis', isActive: true },
          ]}
        />
        <div className="flex flex-col gap-2.5">
          <p className="font-semibold text-2xl tracking-[0.5%] leading-[26px] text-black">
            Test Hypothesis
          </p>
          <p className="font-medium text-sm tracking-[0.5%] leading-[16px] text-neutral-800">
            Generated for: Onboarding process too confusing
          </p>
        </div>
        <div className="flex flex-col gap-5">
          {hypotheses.map((hypothesis, index) => (
            <HypothesisContainer
              key={index}
              hypothesis={hypothesis}
              title={sampleData[index].title}
              primaryMetric={sampleData[index].primaryMetric}
              secondaryMetric={sampleData[index].secondaryMetric}
              impactPercentage={sampleData[index].impactPercentage}
              impactLevel={sampleData[index].impactLevel}
              inspiration={sampleData[index].inspiration}
              onHypothesisChange={(updatedHypothesis) =>
                handleHypothesisChange(index, updatedHypothesis)
              }
            />
          ))}
        </div>
      </div>
    </Dashboard>
  );
}
