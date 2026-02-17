'use client';

import { useEffect, useState } from 'react';
import { fetchDashboardStats, DashboardStats } from '@/lib/api';

export default function Overview() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardStats()
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const getChangeStyles = (changeType: 'positive' | 'negative') => {
    return changeType === 'positive'
      ? 'rounded-[8px] border border-success bg-success p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-success'
      : 'rounded-[8px] border border-unconnected bg-unconnected p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-unconnected';
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-5">
        <div className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
          Overview
        </div>
        <div className="col-span-12">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 xl:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex flex-col justify-between rounded-[8px] bg-white px-3.5 py-4 gap-5 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-24" />
                <div className="h-8 bg-gray-200 rounded w-16" />
                <div className="h-5 bg-gray-200 rounded w-32" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex flex-col gap-5">
        <div className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
          Overview
        </div>
        <div className="text-red-500 text-sm">
          {error || 'Failed to load dashboard stats'}
        </div>
      </div>
    );
  }

  const changeType: 'positive' | 'negative' = stats.change_vs_last_month?.startsWith('-') ? 'negative' : 'positive';

  const dashboardCards = [
    {
      title: 'Tickets Analyzed',
      value: String(stats.ticket_count),
      change: `${stats.change_vs_last_month} vs last month`,
      changeType,
    },
    {
      title: 'Pain Points',
      value: String(stats.cluster_count),
      change: `${stats.classified_count} classified tickets`,
      changeType: 'positive' as const,
    },
    {
      title: 'Hypotheses Generated',
      value: String(stats.hypothesis_count),
      change: `${stats.change_vs_last_month} vs last month`,
      changeType,
    },
    {
      title: 'Experiments Created',
      value: String(stats.experiment_count),
      subtitle: `out of ${stats.hypothesis_count} hypotheses`,
      change: `${stats.change_vs_last_month} vs last month`,
      changeType,
    },
  ];

  return (
    <div className="flex flex-col gap-5">
      <div className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
        Overview
      </div>
      <div className="col-span-12">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 xl:grid-cols-4">
          {dashboardCards.map((card, index) => (
            <div
              key={index}
              className="flex flex-col justify-between rounded-[8px] bg-white px-3.5 py-4 gap-5">
              <div className="flex flex-col gap-5">
                <div className="text-[#7F7F7F] text-sm tracking-[0.5%] leading-[16px] font-semibold">
                  {card.title}
                </div>
                <div className="flex flex-col gap-1.5">
                  <div className="text-2xl font-semibold text-black leading-[26px] tracking-[0.5%]">
                    {card.value}
                  </div>
                  {'subtitle' in card && card.subtitle && (
                    <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                      {card.subtitle}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-start gap-1">
                <span className={getChangeStyles(card.changeType)}>
                  {card.change}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
