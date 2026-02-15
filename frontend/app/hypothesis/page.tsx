'use client';

import { Dashboard } from '@/components/Dashboard';
import HypothesisContainer from '@/components/UI/HypothesisContainer';
import Breadcrumb from '@/components/UI/Breadcrumb';
import { useState, useEffect } from 'react';
import type { Hypothesis } from '@/types';
import { fetchHypotheses, updateHypothesis as apiUpdateHypothesis, type HypothesisData } from '@/lib/api';

function parseHypothesisText(text: string): { ifText: string; thenText: string } {
  // Parse "If X, then Y because Z" format
  const lower = text.toLowerCase();
  const ifIdx = lower.indexOf('if ');
  const thenIdx = lower.indexOf(', then ');
  if (ifIdx !== -1 && thenIdx !== -1) {
    return {
      ifText: text.slice(ifIdx + 3, thenIdx),
      thenText: text.slice(thenIdx + 7),
    };
  }
  return { ifText: text, thenText: '' };
}

function getImpactLevel(score: number | null): 'High' | 'Medium' | 'Low' {
  if (!score) return 'Medium';
  if (score >= 0.8) return 'High';
  if (score >= 0.5) return 'Medium';
  return 'Low';
}

function getMetricFromConfig(config: Record<string, string> | null, key: string): string {
  if (!config) return 'conversion-rate';
  const val = config[key];
  if (!val) return 'conversion-rate';
  // Convert snake_case metric names to kebab-case
  return val.replace(/_/g, '-');
}

export default function HypothesisPage() {
  const [apiHypotheses, setApiHypotheses] = useState<HypothesisData[]>([]);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHypotheses()
      .then((data) => {
        setApiHypotheses(data.hypotheses);
        // Convert API hypotheses to the frontend Hypothesis type
        const converted: Hypothesis[] = data.hypotheses.map((h) => {
          const parsed = parseHypothesisText(h.hypothesis_text);
          const config = h.experiment_config || {};
          return {
            checked: false,
            editMode: { if: false, then: false, variantA: false, variantB: false },
            current: {
              if: parsed.ifText,
              then: parsed.thenText,
              variantA: config.variant_a || 'Current implementation',
              variantB: config.variant_b || 'New proposed solution',
            },
            temp: {
              if: parsed.ifText,
              then: parsed.thenText,
              variantA: config.variant_a || 'Current implementation',
              variantB: config.variant_b || 'New proposed solution',
            },
          };
        });
        setHypotheses(converted);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleHypothesisChange = (index: number, updatedHypothesis: Hypothesis) => {
    const newHypotheses = [...hypotheses];
    newHypotheses[index] = updatedHypothesis;
    setHypotheses(newHypotheses);

    // If saving (edit mode toggled off), persist to API
    const wasEditing = hypotheses[index].editMode;
    const nowEditing = updatedHypothesis.editMode;
    const savedField = (Object.keys(wasEditing) as Array<keyof typeof wasEditing>).find(
      (k) => wasEditing[k] && !nowEditing[k]
    );
    if (savedField && apiHypotheses[index]) {
      const h = apiHypotheses[index];
      const newText = `If ${updatedHypothesis.current.if}, then ${updatedHypothesis.current.then}`;
      const newConfig = {
        ...(h.experiment_config || {}),
        variant_a: updatedHypothesis.current.variantA,
        variant_b: updatedHypothesis.current.variantB,
      };
      apiUpdateHypothesis(h.id, {
        hypothesis_text: newText,
        experiment_config: newConfig,
      }).catch(() => {});
    }
  };

  const sampleMetadata = apiHypotheses.map((h, i) => ({
    title: `Hypothesis ${i + 1}`,
    primaryMetric: getMetricFromConfig(h.experiment_config, 'primary_metric'),
    secondaryMetric: getMetricFromConfig(h.experiment_config, 'secondary_metric'),
    impactPercentage: h.confidence_score ? Math.round(h.confidence_score * 100) : 50,
    impactLevel: getImpactLevel(h.confidence_score),
    inspiration: h.cluster_label
      ? `Based on analysis of "${h.cluster_label}" pain point cluster`
      : 'Generated from ticket analysis',
  }));

  if (loading) {
    return (
      <Dashboard>
        <div className="flex items-center justify-center h-64 text-gray-400">Loading hypotheses...</div>
      </Dashboard>
    );
  }

  if (error) {
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
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
            Failed to load hypotheses: {error}
          </div>
        </div>
      </Dashboard>
    );
  }

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
            {apiHypotheses.length} hypotheses generated from pain point analysis
          </p>
        </div>
        <div className="flex flex-col gap-5">
          {hypotheses.map((hypothesis, index) => (
            <HypothesisContainer
              key={index}
              hypothesis={hypothesis}
              title={sampleMetadata[index]?.title || `Hypothesis ${index + 1}`}
              primaryMetric={sampleMetadata[index]?.primaryMetric || 'conversion-rate'}
              secondaryMetric={sampleMetadata[index]?.secondaryMetric || 'time-to-completion'}
              impactPercentage={sampleMetadata[index]?.impactPercentage || 50}
              impactLevel={sampleMetadata[index]?.impactLevel || 'Medium'}
              inspiration={sampleMetadata[index]?.inspiration || 'Generated from analysis'}
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
