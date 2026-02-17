'use client';

import { Dashboard } from '@/components/Dashboard';
import Breadcrumb from '@/components/UI/Breadcrumb';
import { useEffect, useState } from 'react';
import { fetchHypotheses, updateHypothesis, HypothesisData } from '@/lib/api';

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<HypothesisData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadExperiments();
  }, []);

  const loadExperiments = () => {
    setLoading(true);
    fetchHypotheses()
      .then((res) => {
        const exps = res.hypotheses.filter(
          (h) => h.status === 'experiment' || h.status === 'testing'
        );
        setExperiments(exps);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      await updateHypothesis(id, { status: newStatus });
      loadExperiments();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update';
      setError(message);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'testing':
        return 'bg-[#FFFBE3] border-[#FFE4B6] text-[#F09800]';
      case 'experiment':
        return 'bg-[#F1F3FF] border-[#BEC2E5] text-[#5927FF]';
      default:
        return 'bg-[#F6F6F6] border-[#E8E8E8] text-[#7F7F7F]';
    }
  };

  const getImpactBadge = (impact: string | null) => {
    switch (impact) {
      case 'high':
        return 'bg-success border-success text-success';
      case 'medium':
        return 'bg-[#FFFBE3] border-[#FFE4B6] text-[#F09800]';
      case 'low':
        return 'bg-[#FFF2F2] border-[#FFDCDC] text-[#F71111]';
      default:
        return 'bg-[#F6F6F6] border-[#E8E8E8] text-[#7F7F7F]';
    }
  };

  return (
    <Dashboard>
      <div className="flex flex-col gap-5">
        <Breadcrumb
          items={[
            { label: 'Dashboard', href: '/' },
            { label: 'Experiments', isActive: true },
          ]}
        />
        <div className="flex flex-col gap-2.5">
          <p className="font-semibold text-2xl tracking-[0.5%] leading-[26px] text-black">
            Experiments
          </p>
          <p className="font-medium text-sm tracking-[0.5%] leading-[16px] text-neutral-800">
            Track and manage your A/B tests and experiments.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-600 text-sm">
            {error}
            <button onClick={() => setError(null)} className="ml-2 underline">Dismiss</button>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-pulse text-[#7F7F7F] text-sm">Loading experiments...</div>
          </div>
        ) : experiments.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <p className="text-[#7F7F7F] text-sm tracking-[0.5%] leading-[16px] font-normal">
              No experiments running yet. Push hypotheses to experiments from the Hypothesis page.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {experiments.map((exp) => {
              const config = exp.experiment_config || {};
              return (
                <div
                  key={exp.id}
                  className="bg-primary rounded-xl p-5 flex flex-col gap-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <p className="font-semibold text-lg text-black">
                        Experiment #{exp.id}
                      </p>
                      <span className={`px-2.5 py-1 rounded-lg border text-xs font-medium ${getStatusBadge(exp.status)}`}>
                        {exp.status}
                      </span>
                      <span className={`px-2.5 py-1 rounded-lg border text-xs font-medium ${getImpactBadge(exp.expected_impact)}`}>
                        {exp.expected_impact || 'unknown'} impact
                      </span>
                    </div>
                    <div className="flex gap-2">
                      {exp.status === 'experiment' && (
                        <button
                          onClick={() => handleStatusChange(exp.id, 'testing')}
                          className="px-3 py-1.5 text-xs bg-[#5927FF] text-white rounded-lg hover:bg-[#4a1fd9] transition-colors">
                          Start Testing
                        </button>
                      )}
                      {exp.status === 'testing' && (
                        <button
                          onClick={() => handleStatusChange(exp.id, 'completed')}
                          className="px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                          Mark Complete
                        </button>
                      )}
                      <button
                        onClick={() => handleStatusChange(exp.id, 'draft')}
                        className="px-3 py-1.5 text-xs bg-[#E8E8E8] text-black rounded-lg hover:bg-[#d0d0d0] transition-colors">
                        Back to Draft
                      </button>
                    </div>
                  </div>

                  <p className="text-sm text-black leading-[20px]">
                    {exp.hypothesis_text}
                  </p>

                  {exp.cluster_label && (
                    <p className="text-xs text-[#7F7F7F]">
                      Pain Point: {exp.cluster_label}
                    </p>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-[#F6F6F6] rounded-lg p-3">
                      <p className="text-xs font-medium text-[#7F7F7F] mb-1">Variant A (Control)</p>
                      <p className="text-sm text-black">{config.variant_a || 'Not configured'}</p>
                    </div>
                    <div className="bg-[#F6F6F6] rounded-lg p-3">
                      <p className="text-xs font-medium text-[#7F7F7F] mb-1">Variant B (Test)</p>
                      <p className="text-sm text-black">{config.variant_b || 'Not configured'}</p>
                    </div>
                  </div>

                  <div className="flex gap-6 text-xs text-[#7F7F7F]">
                    {config.primary_metric && (
                      <span>Primary: <span className="text-black font-medium">{config.primary_metric.replace(/_/g, ' ')}</span></span>
                    )}
                    {config.secondary_metric && (
                      <span>Secondary: <span className="text-black font-medium">{config.secondary_metric.replace(/_/g, ' ')}</span></span>
                    )}
                    {config.duration_days && (
                      <span>Duration: <span className="text-black font-medium">{config.duration_days} days</span></span>
                    )}
                    {exp.confidence_score !== null && (
                      <span>Confidence: <span className="text-black font-medium">{Math.round(exp.confidence_score * 100)}%</span></span>
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
