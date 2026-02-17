'use client';

import { Dashboard } from '@/components/Dashboard';
import HypothesisContainer from '@/components/UI/HypothesisContainer';
import Breadcrumb from '@/components/UI/Breadcrumb';
import { useState, useEffect } from 'react';
import type { Hypothesis } from '@/types';
import { fetchHypotheses, createHypothesis, updateHypothesis as updateHypothesisApi, HypothesisData } from '@/lib/api';

function parseHypothesisText(text: string): { if_part: string; then_part: string } {
  const lower = text.toLowerCase();
  const ifIdx = lower.indexOf('if ');
  const thenIdx = lower.indexOf(', then ');
  const thenIdx2 = lower.indexOf(' then ');

  if (ifIdx !== -1 && thenIdx !== -1) {
    return {
      if_part: text.substring(ifIdx + 3, thenIdx).trim(),
      then_part: text.substring(thenIdx + 7).trim(),
    };
  } else if (ifIdx !== -1 && thenIdx2 !== -1) {
    return {
      if_part: text.substring(ifIdx + 3, thenIdx2).trim(),
      then_part: text.substring(thenIdx2 + 6).trim(),
    };
  }
  return { if_part: text, then_part: '' };
}

function getImpactLevel(score: number | null): 'High' | 'Medium' | 'Low' {
  if (!score) return 'Low';
  if (score >= 0.8) return 'High';
  if (score >= 0.5) return 'Medium';
  return 'Low';
}

function apiToUiHypothesis(h: HypothesisData): Hypothesis {
  const parsed = parseHypothesisText(h.hypothesis_text);
  const config = h.experiment_config || {};
  return {
    checked: false,
    editMode: { if: false, then: false, variantA: false, variantB: false },
    current: {
      if: parsed.if_part,
      then: parsed.then_part,
      variantA: config.variant_a || 'Control variant',
      variantB: config.variant_b || 'Test variant',
    },
    temp: {
      if: parsed.if_part,
      then: parsed.then_part,
      variantA: config.variant_a || 'Control variant',
      variantB: config.variant_b || 'Test variant',
    },
  };
}

export default function HypothesisPage() {
  const [apiHypotheses, setApiHypotheses] = useState<HypothesisData[]>([]);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newHypText, setNewHypText] = useState('');
  const [newConfidence, setNewConfidence] = useState('0.7');
  const [newImpact, setNewImpact] = useState('medium');
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState<number | null>(null);

  useEffect(() => {
    loadHypotheses();
  }, []);

  const loadHypotheses = () => {
    setLoading(true);
    fetchHypotheses()
      .then((res) => {
        setApiHypotheses(res.hypotheses);
        setHypotheses(res.hypotheses.map(apiToUiHypothesis));
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const handleHypothesisChange = (index: number, updatedHypothesis: Hypothesis) => {
    const newHypotheses = [...hypotheses];
    newHypotheses[index] = updatedHypothesis;
    setHypotheses(newHypotheses);
  };

  const handleSaveToApi = async (index: number) => {
    const apiH = apiHypotheses[index];
    const uiH = hypotheses[index];
    if (!apiH) return;

    setSaving(index);
    try {
      const hypothesisText = `If ${uiH.current.if}, then ${uiH.current.then}`;
      await updateHypothesisApi(apiH.id, {
        hypothesis_text: hypothesisText,
        experiment_config: {
          ...apiH.experiment_config,
          variant_a: uiH.current.variantA,
          variant_b: uiH.current.variantB,
        },
      });
      loadHypotheses();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to save';
      setError(message);
    } finally {
      setSaving(null);
    }
  };

  const handleCreate = async () => {
    if (!newHypText.trim()) return;
    setCreating(true);
    try {
      await createHypothesis({
        hypothesis_text: newHypText,
        confidence_score: parseFloat(newConfidence) || 0.7,
        expected_impact: newImpact,
        status: 'draft',
      });
      setNewHypText('');
      setNewConfidence('0.7');
      setNewImpact('medium');
      setShowCreate(false);
      loadHypotheses();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create';
      setError(message);
    } finally {
      setCreating(false);
    }
  };

  const handlePushToExperiment = async (index: number) => {
    const apiH = apiHypotheses[index];
    if (!apiH) return;
    try {
      await updateHypothesisApi(apiH.id, { status: 'experiment' });
      loadHypotheses();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update status';
      setError(message);
    }
  };

  if (loading) {
    return (
      <Dashboard>
        <div className="flex flex-col gap-5">
          <Breadcrumb
            items={[
              { label: 'Dashboard', href: '/' },
              { label: 'Hypothesis', isActive: true },
            ]}
          />
          <div className="flex items-center justify-center py-20">
            <div className="animate-pulse text-[#7F7F7F] text-sm">Loading hypotheses...</div>
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
            { label: 'Hypothesis', isActive: true },
          ]}
        />
        <div className="flex flex-row items-center justify-between">
          <div className="flex flex-col gap-2.5">
            <p className="font-semibold text-2xl tracking-[0.5%] leading-[26px] text-black">
              Hypotheses
            </p>
            <p className="font-medium text-sm tracking-[0.5%] leading-[16px] text-neutral-800">
              {apiHypotheses.length} hypotheses generated from pain point analysis
            </p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-4 py-2.5 bg-[#5927FF] text-white rounded-lg text-sm font-medium hover:bg-[#4a1fd9] transition-colors">
            {showCreate ? 'Cancel' : '+ New Hypothesis'}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-600 text-sm">
            {error}
            <button onClick={() => setError(null)} className="ml-2 underline">Dismiss</button>
          </div>
        )}

        {showCreate && (
          <div className="bg-primary p-4 rounded-xl flex flex-col gap-4 border border-[#E8E8E8]">
            <p className="font-semibold text-lg">Create New Hypothesis</p>
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-[#7F7F7F]">Hypothesis Text</label>
              <textarea
                value={newHypText}
                onChange={(e) => setNewHypText(e.target.value)}
                placeholder="If we implement X, then Y will improve because Z"
                className="w-full border border-[#E8E8E8] rounded-lg p-3 text-sm min-h-[80px] resize-none focus:outline-none focus:border-[#5927FF]"
              />
            </div>
            <div className="flex gap-4">
              <div className="flex flex-col gap-2 flex-1">
                <label className="text-sm font-medium text-[#7F7F7F]">Confidence Score (0-1)</label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={newConfidence}
                  onChange={(e) => setNewConfidence(e.target.value)}
                  className="border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]"
                />
              </div>
              <div className="flex flex-col gap-2 flex-1">
                <label className="text-sm font-medium text-[#7F7F7F]">Expected Impact</label>
                <select
                  value={newImpact}
                  onChange={(e) => setNewImpact(e.target.value)}
                  className="border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]">
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>
            <button
              onClick={handleCreate}
              disabled={creating || !newHypText.trim()}
              className="self-end px-4 py-2.5 bg-[#5927FF] text-white rounded-lg text-sm font-medium hover:bg-[#4a1fd9] transition-colors disabled:opacity-50">
              {creating ? 'Creating...' : 'Create Hypothesis'}
            </button>
          </div>
        )}

        {hypotheses.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <p className="text-[#7F7F7F] text-sm tracking-[0.5%] leading-[16px] font-normal">
              No hypotheses generated yet. Run the analysis pipeline to generate hypotheses from pain points.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-5">
            {hypotheses.map((hypothesis, index) => {
              const apiH = apiHypotheses[index];
              const confidenceScore = apiH?.confidence_score ?? 0;
              const impactLevel = getImpactLevel(apiH?.confidence_score ?? null);
              const config = apiH?.experiment_config || {};

              return (
                <div key={apiH?.id ?? index} className="relative">
                  <HypothesisContainer
                    hypothesis={hypothesis}
                    title={`Hypothesis ${index + 1}${apiH?.cluster_label ? ` — ${apiH.cluster_label}` : ''}`}
                    primaryMetric={config.primary_metric || 'conversion-rate'}
                    secondaryMetric={config.secondary_metric || 'user-satisfaction'}
                    impactPercentage={Math.round(confidenceScore * 100)}
                    impactLevel={impactLevel}
                    inspiration={apiH?.cluster_label ? `Generated from pain point: ${apiH.cluster_label}` : 'AI-generated hypothesis'}
                    onHypothesisChange={(updatedHypothesis) =>
                      handleHypothesisChange(index, updatedHypothesis)
                    }
                  />
                  <div className="flex gap-2 mt-2 justify-end">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      apiH?.status === 'experiment' || apiH?.status === 'testing'
                        ? 'bg-[#F1F3FF] text-[#5927FF]'
                        : apiH?.status === 'draft'
                        ? 'bg-[#F6F6F6] text-[#7F7F7F]'
                        : 'bg-success text-success'
                    }`}>
                      {apiH?.status || 'draft'}
                    </span>
                    <button
                      onClick={() => handleSaveToApi(index)}
                      disabled={saving === index}
                      className="px-3 py-1 text-xs bg-[#E8E8E8] rounded hover:bg-[#d0d0d0] transition-colors disabled:opacity-50">
                      {saving === index ? 'Saving...' : 'Save Changes'}
                    </button>
                    {apiH?.status === 'draft' && (
                      <button
                        onClick={() => handlePushToExperiment(index)}
                        className="px-3 py-1 text-xs bg-[#5927FF] text-white rounded hover:bg-[#4a1fd9] transition-colors">
                        Push to Experiment
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Dashboard>
  );
}
