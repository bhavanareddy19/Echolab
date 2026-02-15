'use client';

import { Dashboard } from '@/components/Dashboard';
import Breadcrumb from '@/components/UI/Breadcrumb';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { fetchTicket, updateTicket, deleteTicket, type TicketData } from '@/lib/api';

export default function TicketDetailPage() {
  const params = useParams();
  const router = useRouter();
  const ticketId = Number(params.id);

  const [ticket, setTicket] = useState<TicketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({ title: '', description: '', priority: '', status: '' });

  useEffect(() => {
    if (!ticketId) return;
    setLoading(true);
    fetchTicket(ticketId)
      .then((t) => {
        setTicket(t);
        setEditData({
          title: t.title || '',
          description: t.description || '',
          priority: t.priority || '',
          status: t.status || '',
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ticketId]);

  const handleSave = async () => {
    try {
      await updateTicket(ticketId, editData);
      setEditing(false);
      const updated = await fetchTicket(ticketId);
      setTicket(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to update');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this ticket?')) return;
    try {
      await deleteTicket(ticketId);
      router.push('/tickets');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to delete');
    }
  };

  const getPriorityColor = (priority: string | null) => {
    switch (priority) {
      case 'Critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'High': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'Medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'Low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (loading) {
    return (
      <Dashboard>
        <div className="flex items-center justify-center h-64 text-gray-400">Loading ticket...</div>
      </Dashboard>
    );
  }

  if (error || !ticket) {
    return (
      <Dashboard>
        <div className="flex flex-col items-center justify-center h-64 gap-3">
          <p className="text-red-500">{error || 'Ticket not found'}</p>
          <button onClick={() => router.push('/tickets')} className="text-sm text-[#4652DC] underline">
            Back to tickets
          </button>
        </div>
      </Dashboard>
    );
  }

  return (
    <Dashboard>
      <div className="flex flex-col gap-5 max-w-4xl">
        <Breadcrumb
          items={[
            { label: 'Dashboard', href: '/' },
            { label: 'Tickets', href: '/tickets' },
            { label: ticket.ticket_key, isActive: true },
          ]}
        />

        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-3">
              <span className="font-mono text-[#4652DC] font-semibold">{ticket.ticket_key}</span>
              <span className={`text-xs px-2 py-1 rounded-full border ${getPriorityColor(ticket.priority)}`}>
                {ticket.priority}
              </span>
              <span className="text-xs px-2 py-1 rounded-full border border-gray-200 bg-gray-50 text-gray-600">
                {ticket.status}
              </span>
            </div>
            {editing ? (
              <input
                value={editData.title}
                onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                className="text-xl font-semibold border rounded-lg px-2 py-1 mt-1"
              />
            ) : (
              <h1 className="text-xl font-semibold text-black mt-1">{ticket.title}</h1>
            )}
          </div>
          <div className="flex gap-2">
            {editing ? (
              <>
                <button onClick={() => setEditing(false)} className="px-3 py-1.5 rounded-lg border text-sm">Cancel</button>
                <button onClick={handleSave} className="px-3 py-1.5 rounded-lg bg-black text-white text-sm">Save</button>
              </>
            ) : (
              <>
                <button onClick={() => setEditing(true)} className="px-3 py-1.5 rounded-lg border text-sm">Edit</button>
                <button onClick={handleDelete} className="px-3 py-1.5 rounded-lg border border-red-200 text-red-600 text-sm">Delete</button>
              </>
            )}
          </div>
        </div>

        {/* Description */}
        <div className="bg-white rounded-lg p-4 border border-[#E8E8E8]">
          <h3 className="text-sm font-semibold text-[#7F7F7F] mb-2">Description</h3>
          {editing ? (
            <textarea
              value={editData.description}
              onChange={(e) => setEditData({ ...editData, description: e.target.value })}
              rows={4}
              className="w-full border rounded-lg px-3 py-2 text-sm outline-none resize-none"
            />
          ) : (
            <p className="text-sm text-gray-800 whitespace-pre-wrap">{ticket.description || 'No description provided.'}</p>
          )}
        </div>

        {/* Edit priority/status */}
        {editing && (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-4 border border-[#E8E8E8]">
              <label className="text-sm font-semibold text-[#7F7F7F] mb-2 block">Priority</label>
              <select
                value={editData.priority}
                onChange={(e) => setEditData({ ...editData, priority: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm outline-none">
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
            <div className="bg-white rounded-lg p-4 border border-[#E8E8E8]">
              <label className="text-sm font-semibold text-[#7F7F7F] mb-2 block">Status</label>
              <select
                value={editData.status}
                onChange={(e) => setEditData({ ...editData, status: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm outline-none">
                <option value="Open">Open</option>
                <option value="In Progress">In Progress</option>
                <option value="Resolved">Resolved</option>
                <option value="Closed">Closed</option>
              </select>
            </div>
          </div>
        )}

        {/* Classification Results */}
        <div className="bg-white rounded-lg p-4 border border-[#E8E8E8]">
          <h3 className="text-sm font-semibold text-[#7F7F7F] mb-3">AI Classification</h3>
          {ticket.feature_type ? (
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <span className="text-xs text-[#7F7F7F]">Feature Type</span>
                <span className="text-sm font-medium capitalize">{ticket.feature_type}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs text-[#7F7F7F]">Sentiment</span>
                <span className={`text-sm font-medium capitalize ${
                  ticket.sentiment === 'negative' ? 'text-red-600' :
                  ticket.sentiment === 'positive' ? 'text-green-600' : 'text-gray-600'
                }`}>{ticket.sentiment}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs text-[#7F7F7F]">Urgency Score</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        (ticket.urgency_score ?? 0) > 0.7 ? 'bg-red-500' :
                        (ticket.urgency_score ?? 0) > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${(ticket.urgency_score ?? 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm">{((ticket.urgency_score ?? 0) * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs text-[#7F7F7F]">Cluster ID</span>
                <span className="text-sm font-medium">{ticket.cluster_id ?? 'Unassigned'}</span>
              </div>
              {ticket.customer_problem && (
                <div className="col-span-2 flex flex-col gap-1">
                  <span className="text-xs text-[#7F7F7F]">Customer Problem</span>
                  <span className="text-sm">{ticket.customer_problem}</span>
                </div>
              )}
              {ticket.root_cause && (
                <div className="col-span-2 flex flex-col gap-1">
                  <span className="text-xs text-[#7F7F7F]">Root Cause</span>
                  <span className="text-sm">{ticket.root_cause}</span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400">Not yet classified. Run analysis to classify this ticket.</p>
          )}
        </div>

        {/* Metadata */}
        <div className="bg-white rounded-lg p-4 border border-[#E8E8E8]">
          <h3 className="text-sm font-semibold text-[#7F7F7F] mb-3">Metadata</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <span className="text-xs text-[#7F7F7F]">Reporter</span>
              <span className="text-sm">{ticket.reporter || 'Unknown'}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs text-[#7F7F7F]">Product</span>
              <span className="text-sm">{ticket.product || 'N/A'}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs text-[#7F7F7F]">Component</span>
              <span className="text-sm">{ticket.component || 'N/A'}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs text-[#7F7F7F]">Created</span>
              <span className="text-sm">{ticket.created_at ? new Date(ticket.created_at).toLocaleDateString() : 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>
    </Dashboard>
  );
}
