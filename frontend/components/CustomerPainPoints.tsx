'use client';

import { IconTrendingUp, IconTrendingDown } from '@tabler/icons-react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { fetchClusters, type ClusterData } from '@/lib/api';

export default function CustomerPainPoints() {
  const router = useRouter();
  const [clusters, setClusters] = useState<ClusterData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchClusters()
      .then((data) => setClusters(data.clusters.slice(0, 3)))
      .catch((e) => setError(e.message));
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

  const getClusterTags = (cluster: ClusterData) => {
    const tags: { label: string; color: string }[] = [];
    if (cluster.avg_urgency && cluster.avg_urgency > 0.7) {
      tags.push({ label: 'Bug', color: 'red' });
    } else {
      tags.push({ label: 'Feature', color: 'blue' });
    }
    if (cluster.status === 'active') {
      tags.push({ label: 'Active', color: 'yellow' });
    }
    return tags;
  };

  const totalTickets = clusters.reduce((sum, c) => sum + c.num_tickets, 0);

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
          {error
            ? 'Failed to load pain points'
            : `Top themes identified from ${totalTickets} tickets`}
        </p>
      </div>

      <div className="col-span-12">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 xl:grid-cols-3">
          {clusters.map((cluster) => {
            const tags = getClusterTags(cluster);
            const isHighUrgency = (cluster.avg_urgency || 0) > 0.7;
            return (
              <div
                key={cluster.id}
                className="flex flex-col justify-between rounded-[8px] bg-primary py-4 px-3 gap-5 cursor-pointer hover:!bg-[#E8E8E8] hover:scale-102 transition-all duration-200"
                onClick={() => router.push(`/painpoints?cluster=${cluster.id}`)}>
                <div className="flex flex-row items-center justify-between">
                  <div className="text-[#7F7F7F] text-sm font-semibold leading-[16px] tracking-[0.5%]">
                    {cluster.cluster_label}
                  </div>
                  <div className="flex gap-1">
                    {tags.map((tag, tagIndex) => (
                      <div key={tagIndex} className={getTagStyles(tag.color)}>
                        {tag.label}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex flex-row items-center justify-between">
                  <div className="flex flex-col gap-1.5">
                    <div className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                      {cluster.num_tickets}
                    </div>
                    <div className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                      Tickets
                    </div>
                  </div>
                  <div className="flex flex-col gap-1.5 items-end">
                    <div className="flex items-center gap-1">
                      {isHighUrgency ? (
                        <IconTrendingUp className="w-5 h-5 text-[#F71111]" stroke={1.5} />
                      ) : (
                        <IconTrendingDown className="w-5 h-5 text-[#5927FF]" stroke={1.5} />
                      )}
                      <div
                        className={`text-sm font-normal leading-[16px] tracking-[0.5%] ${
                          isHighUrgency ? 'text-[#F71111]' : 'text-[#5927FF]'
                        }`}>
                        {cluster.avg_urgency ? `${Math.round(cluster.avg_urgency * 100)}%` : 'N/A'}
                      </div>
                    </div>
                    <div className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                      avg urgency
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
