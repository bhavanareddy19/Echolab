'use client';

import { Dashboard } from '@/components/Dashboard';
import Breadcrumb from '@/components/UI/Breadcrumb';
import { useEffect, useState } from 'react';
import { fetchHypotheses, type HypothesisData } from '@/lib/api';
import { IconFlask, IconClock, IconChartBar } from '@tabler/icons-react';

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<HypothesisData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHypotheses()
      .then((data) => {
        // Show hypotheses that have been pushed to experiment/testing status
        const exps = data.hypotheses.filter(
          (h) => h.status === 'experiment' || h.status === 'testing'
        );
        setExperiments(exps);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'testing':
        return 'border-green-200 bg-green-50 text-green-600';
      case 'experiment':
        return 'border-blue-200 bg-blue-50 text-blue-600';
      default:
        return 'border-gray-200 bg-gray-50 text-gray-600';
    }
  };

  const getImpactColor = (impact: string | null) => {
    switch (impact) {
      case 'high':
        return 'border-green-200 bg-green-50 text-green-600';
      case 'medium':
        return 'border-yellow-200 bg-yellow-50 text-yellow-600';
      case 'low':
        return 'border-red-200 bg-red-50 text-red-600';
      default:
        return 'border-gray-200 bg-gray-50 text-gray-600';
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

        <div className="flex flex-col gap-1">
          <p className="font-semibold text-2xl tracking-[0.5%] leading-[26px] text-black">
            Experiments
          </p>
          <p className="text-[#7F7F7F] text-sm">
            Hypotheses pushed to A/B testing
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-gray-400 text-center py-12">Loading experiments...</div>
        ) : experiments.length === 0 ? (
          <div className="text-center py-16 flex flex-col items-center gap-3">
            <IconFlask className="w-12 h-12 text-gray-300" />
            <p className="text-gray-400">No active experiments yet.</p>
            <p className="text-gray-400 text-sm">
              Push hypotheses from the Hypothesis page to create experiments.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {experiments.map((exp) => {
              const config = exp.experiment_config || {};
              return (
                <div
                  key={exp.id}
                  className="bg-white rounded-lg border border-[#E8E8E8] p-5 flex flex-col gap-4">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center gap-2">
                        <IconFlask className="w-5 h-5 text-[#4652DC]" />
                        <h3 className="font-semibold text-base text-black">
                          Experiment #{exp.id}
                        </h3>
                        <span className={`text-xs px-2 py-1 rounded-full border capitalize ${getStatusColor(exp.status)}`}>
                          {exp.status}
                        </span>
                        {exp.expected_impact && (
                          <span className={`text-xs px-2 py-1 rounded-full border capitalize ${getImpactColor(exp.expected_impact)}`}>
                            {exp.expected_impact} impact
                          </span>
                        )}
                      </div>
                      {exp.cluster_label && (
                        <span className="text-xs text-[#7F7F7F]">
                          Cluster: {exp.cluster_label}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1 text-xs text-[#7F7F7F]">
                      <IconClock className="w-3.5 h-3.5" />
                      {config.duration_days ? `${config.duration_days} days` : 'TBD'}
                    </div>
                  </div>

                  {/* Hypothesis text */}
                  <div className="bg-[#F9F9F9] rounded-lg p-3">
                    <p className="text-sm text-gray-700">{exp.hypothesis_text}</p>
                  </div>

                  {/* Config */}
                  {(config.variant_a || config.variant_b) && (
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-[#F6F6F6] rounded-lg p-3">
                        <div className="flex items-center gap-1.5 mb-1.5">
                          <span className="bg-[#E8E8E8] font-bold text-xs rounded w-5 h-5 flex items-center justify-center">A</span>
                          <span className="text-xs font-semibold text-[#7F7F7F]">Control</span>
                        </div>
                        <p className="text-sm">{config.variant_a || 'N/A'}</p>
                      </div>
                      <div className="bg-[#F0F0FF] rounded-lg p-3">
                        <div className="flex items-center gap-1.5 mb-1.5">
                          <span className="bg-[#D4D0FF] font-bold text-xs rounded w-5 h-5 flex items-center justify-center text-[#4652DC]">B</span>
                          <span className="text-xs font-semibold text-[#4652DC]">Variant</span>
                        </div>
                        <p className="text-sm">{config.variant_b || 'N/A'}</p>
                      </div>
                    </div>
                  )}

                  {/* Metrics */}
                  <div className="flex gap-4">
                    {config.primary_metric && (
                      <div className="flex items-center gap-1.5">
                        <IconChartBar className="w-4 h-4 text-[#4652DC]" />
                        <span className="text-xs text-[#7F7F7F]">Primary:</span>
                        <span className="text-xs font-medium">{config.primary_metric.replace(/_/g, ' ')}</span>
                      </div>
                    )}
                    {config.secondary_metric && (
                      <div className="flex items-center gap-1.5">
                        <IconChartBar className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-[#7F7F7F]">Secondary:</span>
                        <span className="text-xs font-medium">{config.secondary_metric.replace(/_/g, ' ')}</span>
                      </div>
                    )}
                  </div>

                  {/* Confidence */}
                  {exp.confidence_score && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#7F7F7F]">Confidence:</span>
                      <div className="w-32 bg-gray-200 rounded-full h-1.5">
                        <div
                          className="brand-gradient h-full rounded-full"
                          style={{ width: `${exp.confidence_score * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium">{Math.round(exp.confidence_score * 100)}%</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Dashboard>
  );
}
