'use client';

import { IconTrendingUp, IconTrendingDown } from '@tabler/icons-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { fetchClusters, ClusterData } from '@/lib/api';

export default function CustomerPainPoints() {
  const router = useRouter();
  const [clusters, setClusters] = useState<ClusterData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchClusters()
      .then((res) => setClusters(res.clusters))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const getTagStyles = (color: string) => {
    switch (color) {
      case 'blue':
        return 'rounded-[8px] border border-[#D4E6FF] bg-[#F6FAFF] p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-[#4652DC]';
      case 'red':
        return 'rounded-[8px] border border-[#FFDCDC] bg-[#FFF2F2] p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-[#F71111]';
      case 'yellow':
        return 'rounded-[8px] border border-[#FFE4B6] bg-[#FFFBE3] p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-[#F09800]';
      case 'gray':
      default:
        return 'rounded-[8px] border border-[#8C8C8C] bg-[#F6F6F6] p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-black';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'yellow';
      case 'resolved': return 'blue';
      default: return 'gray';
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-1.5">
          <p className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
            Customer Pain Points
          </p>
        </div>
        <div className="col-span-12">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 xl:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex flex-col justify-between rounded-[8px] bg-primary py-4 px-3 gap-5 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-32" />
                <div className="h-8 bg-gray-200 rounded w-16" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col gap-5">
        <p className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
          Customer Pain Points
        </p>
        <div className="text-red-500 text-sm">{error}</div>
      </div>
    );
  }

  const totalTickets = clusters.reduce((sum, c) => sum + (c.actual_ticket_count || c.num_tickets), 0);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-1.5">
        <div className="flex flex-row items-center justify-between">
          <p className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
            Customer Pain Points
          </p>
          <div
            className="bg-[#E8E8E8] rounded-[8px] px-3 py-2.5 text-black text-sm tracking-[0.5%] leading-[16px] font-medium cursor-pointer"
            onClick={() => router.push('/painpoints')}>
            View All
          </div>
        </div>

        <p className="text-[#7F7F7F] text-sm tracking-[0.5%] leading-[16px] font-normal">
          Top themes identified from {totalTickets} tickets across {clusters.length} clusters
        </p>
      </div>

      <div className="col-span-12">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 xl:grid-cols-3">
          {clusters.length === 0 ? (
            <div className="col-span-3 flex items-center justify-center py-10">
              <p className="text-[#7F7F7F] text-sm">No pain points identified yet. Run analysis to generate clusters.</p>
            </div>
          ) : (
            clusters.slice(0, 3).map((cluster) => {
              const urgency = cluster.avg_urgency ?? 0;
              const changeType = urgency > 0.5 ? 'negative' : 'positive';
              const urgencyPct = `${Math.round(urgency * 100)}%`;

              return (
                <div
                  key={cluster.id}
                  className="flex flex-col justify-between rounded-[8px] bg-primary py-4 px-3 gap-5 cursor-pointer hover:!bg-[#E8E8E8] hover:scale-102 transition-all duration-200"
                  onClick={() => router.push(`/painpoints`)}>
                  <div className="flex flex-row items-center justify-between">
                    <div className="text-[#7F7F7F] text-sm font-semibold leading-[16px] tracking-[0.5%]">
                      {cluster.cluster_label}
                    </div>
                    <div className="flex gap-1">
                      <div className={getTagStyles(getStatusColor(cluster.status))}>
                        {cluster.status}
                      </div>
                      {cluster.top_keywords?.slice(0, 1).map((kw, i) => (
                        <div key={i} className={getTagStyles('gray')}>
                          {kw}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="flex flex-row items-center justify-between">
                    <div className="flex flex-col gap-1.5">
                      <div className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                        {cluster.actual_ticket_count || cluster.num_tickets}
                      </div>
                      <div className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                        Tickets
                      </div>
                    </div>
                    <div className="flex flex-col gap-1.5 items-end">
                      <div className="flex items-center gap-1">
                        {changeType === 'positive' ? (
                          <IconTrendingDown
                            className="w-5 h-5 text-[#5927FF]"
                            stroke={1.5}
                          />
                        ) : (
                          <IconTrendingUp
                            className="w-5 h-5 text-[#F71111]"
                            stroke={1.5}
                          />
                        )}
                        <div
                          className={`text-sm font-normal leading-[16px] tracking-[0.5%] ${
                            changeType === 'positive'
                              ? 'text-[#5927FF]'
                              : 'text-[#F71111]'
                          }`}>
                          {urgencyPct}
                        </div>
                      </div>
                      <div className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                        avg urgency
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
