'use client';

import { useEffect, useState } from 'react';
import { fetchDashboardStats, DashboardStats } from '@/lib/api';

export default function BugsAndFeatures() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardStats()
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col gap-5">
        <div className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
          Bugs and Features
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="w-full flex justify-between items-center bg-primary rounded-[8px] py-4 px-3 animate-pulse">
              <div className="h-20 bg-gray-200 rounded w-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex flex-col gap-5">
        <div className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
          Bugs and Features
        </div>
        <div className="text-red-500 text-sm">{error || 'Failed to load stats'}</div>
      </div>
    );
  }

  const featureTotal = stats.features;
  const bugTotal = stats.bugs;
  const improvementTotal = stats.improvements;
  const changeText = stats.change_vs_last_month;
  const isPositiveChange = !changeText?.startsWith('-');

  return (
    <div className="flex flex-col gap-5">
      <div className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
        Bugs and Features
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Features */}
        <div className="w-full flex justify-between items-center bg-primary rounded-[8px] py-4 px-3">
          <div className="flex flex-col gap-10">
            <p className="text-[#7F7F7F] text-sm font-semibold leading-[16px] tracking-[0.5%]">
              Features
            </p>
            <div className={`rounded-[8px] border p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium ${
              isPositiveChange
                ? 'border-success bg-success text-success'
                : 'border-[#FFDCDC] bg-[#FFF2F2] text-[#F71111]'
            }`}>
              {changeText} vs last month
            </div>
          </div>
          <div className="flex flex-row items-center justify-between gap-4">
            <div className="flex flex-col gap-1.5">
              <p className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                {featureTotal}
              </p>
              <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                total
              </p>
            </div>
            <div className="w-[1px] h-12 bg-[#E8E8E8]" />
            <div className="flex flex-col gap-1.5">
              <p className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                {improvementTotal}
              </p>
              <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                improvements
              </p>
            </div>
          </div>
        </div>

        {/* Bugs */}
        <div className="w-full flex justify-between items-center bg-primary rounded-[8px] py-4 px-3">
          <div className="flex flex-col gap-10">
            <p className="text-[#7F7F7F] text-sm font-semibold leading-[16px] tracking-[0.5%]">
              Bugs
            </p>
            <div className="rounded-[8px] border border-[#FFDCDC] bg-[#FFF2F2] p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-[#F71111]">
              {bugTotal} reported
            </div>
          </div>
          <div className="flex flex-row items-center justify-between gap-4">
            <div className="flex flex-col gap-1.5">
              <p className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                {bugTotal}
              </p>
              <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                total bugs
              </p>
            </div>
            <div className="w-[1px] h-12 bg-[#E8E8E8]" />
            <div className="flex flex-col gap-1.5">
              <p className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                {stats.classified_count}
              </p>
              <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                classified
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
