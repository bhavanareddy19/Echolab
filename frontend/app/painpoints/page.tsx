'use client';

import { Dashboard } from '@/components/Dashboard';
import Breadcrumb from '@/components/UI/Breadcrumb';
import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { fetchClusters, fetchCluster, type ClusterData, type ClusterDetail } from '@/lib/api';
import { IconTrendingUp, IconArrowLeft } from '@tabler/icons-react';

export default function PainPointsPage() {
  return (
    <Suspense fallback={<Dashboard><div className="text-gray-400 text-center py-12">Loading...</div></Dashboard>}>
      <PainPointsContent />
    </Suspense>
  );
}

function PainPointsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const selectedClusterId = searchParams.get('cluster');

  const [clusters, setClusters] = useState<ClusterData[]>([]);
  const [clusterDetail, setClusterDetail] = useState<ClusterDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedClusterId) {
      setLoading(true);
      fetchCluster(Number(selectedClusterId))
        .then(setClusterDetail)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    } else {
      setLoading(true);
      fetchClusters()
        .then((data) => setClusters(data.clusters))
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [selectedClusterId]);

  const getUrgencyColor = (urgency: number) => {
    if (urgency > 0.7) return 'text-red-600';
    if (urgency > 0.4) return 'text-yellow-600';
    return 'text-green-600';
  };

  // Cluster detail view
  if (selectedClusterId && clusterDetail) {
    return (
      <Dashboard>
        <div className="flex flex-col gap-5">
          <Breadcrumb
            items={[
              { label: 'Dashboard', href: '/' },
              { label: 'Pain Points', href: '/painpoints' },
              { label: clusterDetail.cluster_label, isActive: true },
            ]}
          />

          <button
            onClick={() => router.push('/painpoints')}
            className="flex items-center gap-1 text-sm text-[#4652DC] w-fit">
            <IconArrowLeft className="w-4 h-4" />
            Back to all pain points
          </button>

          {/* Cluster header */}
          <div className="bg-white rounded-lg p-6 border border-[#E8E8E8]">
            <div className="flex items-start justify-between">
              <div className="flex flex-col gap-2">
                <h1 className="text-2xl font-semibold text-black">{clusterDetail.cluster_label}</h1>
                <p className="text-sm text-gray-600">{clusterDetail.description}</p>
              </div>
              <div className="flex gap-6 text-center">
                <div className="flex flex-col gap-1">
                  <span className="text-2xl font-semibold">{clusterDetail.num_tickets}</span>
                  <span className="text-xs text-[#7F7F7F]">Tickets</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className={`text-2xl font-semibold ${getUrgencyColor(clusterDetail.avg_urgency || 0)}`}>
                    {clusterDetail.avg_urgency ? `${Math.round(clusterDetail.avg_urgency * 100)}%` : 'N/A'}
                  </span>
                  <span className="text-xs text-[#7F7F7F]">Avg Urgency</span>
                </div>
              </div>
            </div>

            {/* Keywords */}
            {clusterDetail.top_keywords && (
              <div className="mt-4 flex gap-2 flex-wrap">
                {(clusterDetail.top_keywords as string[]).map((kw, i) => (
                  <span key={i} className="px-2 py-1 rounded-full bg-[#F0F0FF] text-[#4652DC] text-xs">
                    {kw}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Associated tickets */}
          <div className="bg-white rounded-lg border border-[#E8E8E8] overflow-hidden">
            <div className="px-4 py-3 border-b border-[#E8E8E8] bg-[#F9F9F9]">
              <h3 className="text-sm font-semibold text-gray-700">
                Associated Tickets ({clusterDetail.tickets?.length || 0})
              </h3>
            </div>
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#E8E8E8]">
                  <th className="text-left px-4 py-2 text-xs font-semibold text-[#7F7F7F] uppercase">Key</th>
                  <th className="text-left px-4 py-2 text-xs font-semibold text-[#7F7F7F] uppercase">Title</th>
                  <th className="text-left px-4 py-2 text-xs font-semibold text-[#7F7F7F] uppercase">Type</th>
                  <th className="text-left px-4 py-2 text-xs font-semibold text-[#7F7F7F] uppercase">Sentiment</th>
                  <th className="text-left px-4 py-2 text-xs font-semibold text-[#7F7F7F] uppercase">Urgency</th>
                </tr>
              </thead>
              <tbody>
                {clusterDetail.tickets?.map((t) => (
                  <tr
                    key={t.id}
                    className="border-b border-[#F0F0F0] hover:bg-[#F9F9F9] cursor-pointer"
                    onClick={() => router.push(`/tickets/${t.id}`)}>
                    <td className="px-4 py-3 text-sm font-mono text-[#4652DC]">{t.ticket_key}</td>
                    <td className="px-4 py-3 text-sm max-w-xs truncate">{t.title}</td>
                    <td className="px-4 py-3 text-sm capitalize">{t.feature_type || '-'}</td>
                    <td className={`px-4 py-3 text-sm capitalize ${
                      t.sentiment === 'negative' ? 'text-red-600' :
                      t.sentiment === 'positive' ? 'text-green-600' : 'text-gray-600'
                    }`}>{t.sentiment || '-'}</td>
                    <td className="px-4 py-3 text-sm">
                      {t.urgency_score != null ? `${(t.urgency_score * 100).toFixed(0)}%` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Link to hypotheses */}
          <button
            onClick={() => router.push('/hypothesis')}
            className="self-start brand-gradient text-secondary py-2 px-4 rounded-lg font-medium text-sm cursor-pointer">
            View Hypotheses for this Pain Point
          </button>
        </div>
      </Dashboard>
    );
  }

  // Clusters list view
  return (
    <Dashboard>
      <div className="flex flex-col gap-5">
        <Breadcrumb
          items={[
            { label: 'Dashboard', href: '/' },
            { label: 'Pain Points', isActive: true },
          ]}
        />

        <div className="flex flex-col gap-1">
          <p className="font-semibold text-2xl tracking-[0.5%] leading-[26px] text-black">
            Pain Points
          </p>
          <p className="text-[#7F7F7F] text-sm">
            Customer issue clusters identified from ticket analysis
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-gray-400 text-center py-12">Loading pain points...</div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {clusters.map((cluster) => (
              <div
                key={cluster.id}
                className="bg-white rounded-lg border border-[#E8E8E8] p-5 flex flex-col gap-4 cursor-pointer hover:border-[#4652DC] hover:shadow-md transition-all"
                onClick={() => router.push(`/painpoints?cluster=${cluster.id}`)}>
                <div className="flex items-start justify-between">
                  <h3 className="text-base font-semibold text-black">{cluster.cluster_label}</h3>
                  <span className={`text-xs px-2 py-1 rounded-full border ${
                    cluster.status === 'active'
                      ? 'border-green-200 bg-green-50 text-green-600'
                      : 'border-gray-200 bg-gray-50 text-gray-600'
                  }`}>
                    {cluster.status}
                  </span>
                </div>

                <p className="text-sm text-gray-600 line-clamp-2">{cluster.description}</p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex flex-col">
                      <span className="text-lg font-semibold">{cluster.num_tickets}</span>
                      <span className="text-xs text-[#7F7F7F]">tickets</span>
                    </div>
                    <div className="flex flex-col">
                      <span className={`text-lg font-semibold ${getUrgencyColor(cluster.avg_urgency || 0)}`}>
                        {cluster.avg_urgency ? `${Math.round(cluster.avg_urgency * 100)}%` : 'N/A'}
                      </span>
                      <span className="text-xs text-[#7F7F7F]">avg urgency</span>
                    </div>
                  </div>
                  <IconTrendingUp className={`w-5 h-5 ${getUrgencyColor(cluster.avg_urgency || 0)}`} />
                </div>

                {/* Keywords */}
                {cluster.top_keywords && (
                  <div className="flex gap-1.5 flex-wrap">
                    {(cluster.top_keywords as string[]).slice(0, 4).map((kw, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-full bg-[#F6F6F6] text-gray-600 text-xs">
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Dashboard>
  );
}
