'use client';

import { Dashboard } from '@/components/Dashboard';
import Breadcrumb from '@/components/UI/Breadcrumb';
import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  fetchTickets,
  createTicket,
  uploadCSV,
  triggerAnalysis,
  type TicketData,
  type TicketCreatePayload,
} from '@/lib/api';
import { IconPlus, IconUpload, IconSearch, IconPlayerPlay } from '@tabler/icons-react';

export default function TicketsPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [tickets, setTickets] = useState<TicketData[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  // Create ticket modal
  const [showCreate, setShowCreate] = useState(false);
  const [newTicket, setNewTicket] = useState<TicketCreatePayload>({
    ticket_key: '',
    title: '',
    description: '',
    priority: 'Medium',
    status: 'Open',
  });

  // Analysis state
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);

  const loadTickets = useCallback(() => {
    setLoading(true);
    fetchTickets({
      page,
      page_size: 20,
      priority: priorityFilter || undefined,
      status: statusFilter || undefined,
      feature_type: typeFilter || undefined,
      search: searchQuery || undefined,
    })
      .then((data) => {
        setTickets(data.tickets);
        setTotal(data.total);
        setTotalPages(data.total_pages);
        setError(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page, priorityFilter, statusFilter, typeFilter, searchQuery]);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  const handleSearch = () => {
    setPage(1);
    loadTickets();
  };

  const handleCreateTicket = async () => {
    if (!newTicket.ticket_key || !newTicket.title) return;
    try {
      await createTicket(newTicket);
      setShowCreate(false);
      setNewTicket({ ticket_key: '', title: '', description: '', priority: 'Medium', status: 'Open' });
      loadTickets();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create ticket');
    }
  };

  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await uploadCSV(file);
      setAnalysisResult(`Uploaded ${result.inserted} tickets from ${result.filename}`);
      loadTickets();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to upload CSV');
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const result = await triggerAnalysis();
      setAnalysisResult(result.message);
      loadTickets();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Analysis failed');
    }
    setAnalyzing(false);
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

  const getSentimentColor = (sentiment: string | null) => {
    switch (sentiment) {
      case 'negative': return 'text-red-600';
      case 'positive': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <Dashboard>
      <div className="flex flex-col gap-5">
        <Breadcrumb
          items={[
            { label: 'Dashboard', href: '/' },
            { label: 'Tickets', isActive: true },
          ]}
        />

        {/* Header */}
        <div className="flex flex-row items-center justify-between">
          <div className="flex flex-col gap-1">
            <p className="font-semibold text-2xl tracking-[0.5%] leading-[26px] text-black">
              Tickets
            </p>
            <p className="text-[#7F7F7F] text-sm">{total} total tickets</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="flex items-center gap-1.5 brand-gradient text-secondary py-2 px-3 rounded-lg font-medium text-sm cursor-pointer disabled:opacity-50">
              <IconPlayerPlay className="w-4 h-4" />
              {analyzing ? 'Analyzing...' : 'Run Analysis'}
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 bg-[#E8E8E8] text-black py-2 px-3 rounded-lg font-medium text-sm cursor-pointer">
              <IconUpload className="w-4 h-4" />
              Upload CSV
            </button>
            <input ref={fileInputRef} type="file" accept=".csv" className="hidden" onChange={handleCSVUpload} />
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1.5 bg-black text-white py-2 px-3 rounded-lg font-medium text-sm cursor-pointer">
              <IconPlus className="w-4 h-4" />
              Add Ticket
            </button>
          </div>
        </div>

        {/* Status messages */}
        {analysisResult && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-green-700 text-sm flex justify-between items-center">
            {analysisResult}
            <button onClick={() => setAnalysisResult(null)} className="text-green-900 font-bold ml-2">x</button>
          </div>
        )}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm flex justify-between items-center">
            {error}
            <button onClick={() => setError(null)} className="text-red-900 font-bold ml-2">x</button>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-3 flex-wrap">
          <div className="flex items-center bg-white rounded-lg border border-[#E8E8E8] px-3 py-2 gap-2">
            <IconSearch className="w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search tickets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="outline-none text-sm bg-transparent w-48"
            />
          </div>
          <select
            value={priorityFilter}
            onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
            className="bg-white rounded-lg border border-[#E8E8E8] px-3 py-2 text-sm outline-none">
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="bg-white rounded-lg border border-[#E8E8E8] px-3 py-2 text-sm outline-none">
            <option value="">All Statuses</option>
            <option value="Open">Open</option>
            <option value="In Progress">In Progress</option>
            <option value="Resolved">Resolved</option>
            <option value="Closed">Closed</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
            className="bg-white rounded-lg border border-[#E8E8E8] px-3 py-2 text-sm outline-none">
            <option value="">All Types</option>
            <option value="bug">Bug</option>
            <option value="feature">Feature</option>
            <option value="improvement">Improvement</option>
          </select>
        </div>

        {/* Table */}
        <div className="bg-white rounded-lg border border-[#E8E8E8] overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-[#F9F9F9] border-b border-[#E8E8E8]">
                <th className="text-left px-4 py-3 text-xs font-semibold text-[#7F7F7F] uppercase tracking-wider">Key</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-[#7F7F7F] uppercase tracking-wider">Title</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-[#7F7F7F] uppercase tracking-wider">Priority</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-[#7F7F7F] uppercase tracking-wider">Status</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-[#7F7F7F] uppercase tracking-wider">Type</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-[#7F7F7F] uppercase tracking-wider">Sentiment</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-[#7F7F7F] uppercase tracking-wider">Urgency</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-gray-400">Loading...</td>
                </tr>
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-gray-400">No tickets found</td>
                </tr>
              ) : (
                tickets.map((ticket) => (
                  <tr
                    key={ticket.id}
                    className="border-b border-[#F0F0F0] hover:bg-[#F9F9F9] cursor-pointer transition-colors"
                    onClick={() => router.push(`/tickets/${ticket.id}`)}>
                    <td className="px-4 py-3 text-sm font-mono text-[#4652DC]">{ticket.ticket_key}</td>
                    <td className="px-4 py-3 text-sm text-black max-w-xs truncate">{ticket.title}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-1 rounded-full border ${getPriorityColor(ticket.priority)}`}>
                        {ticket.priority || 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{ticket.status || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 capitalize">{ticket.feature_type || '-'}</td>
                    <td className={`px-4 py-3 text-sm capitalize ${getSentimentColor(ticket.sentiment)}`}>
                      {ticket.sentiment || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {ticket.urgency_score != null ? (
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                ticket.urgency_score > 0.7 ? 'bg-red-500' :
                                ticket.urgency_score > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${ticket.urgency_score * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500">{(ticket.urgency_score * 100).toFixed(0)}%</span>
                        </div>
                      ) : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded-lg bg-white border text-sm disabled:opacity-30">
              Previous
            </button>
            <span className="px-3 py-1.5 text-sm text-gray-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 rounded-lg bg-white border text-sm disabled:opacity-30">
              Next
            </button>
          </div>
        )}

        {/* Create Ticket Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-lg flex flex-col gap-4">
              <h2 className="text-xl font-semibold text-black">Create New Ticket</h2>
              <div className="flex flex-col gap-3">
                <div>
                  <label className="text-sm text-gray-600 mb-1 block">Ticket Key *</label>
                  <input
                    type="text"
                    value={newTicket.ticket_key}
                    onChange={(e) => setNewTicket({ ...newTicket, ticket_key: e.target.value })}
                    placeholder="e.g. ECHO-201"
                    className="w-full border rounded-lg px-3 py-2 text-sm outline-none"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-600 mb-1 block">Title *</label>
                  <input
                    type="text"
                    value={newTicket.title}
                    onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })}
                    placeholder="Brief summary of the issue"
                    className="w-full border rounded-lg px-3 py-2 text-sm outline-none"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-600 mb-1 block">Description</label>
                  <textarea
                    value={newTicket.description}
                    onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                    placeholder="Detailed description..."
                    rows={4}
                    className="w-full border rounded-lg px-3 py-2 text-sm outline-none resize-none"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-sm text-gray-600 mb-1 block">Priority</label>
                    <select
                      value={newTicket.priority}
                      onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
                      className="w-full border rounded-lg px-3 py-2 text-sm outline-none">
                      <option value="Critical">Critical</option>
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Low">Low</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm text-gray-600 mb-1 block">Status</label>
                    <select
                      value={newTicket.status}
                      onChange={(e) => setNewTicket({ ...newTicket, status: e.target.value })}
                      className="w-full border rounded-lg px-3 py-2 text-sm outline-none">
                      <option value="Open">Open</option>
                      <option value="In Progress">In Progress</option>
                      <option value="Resolved">Resolved</option>
                      <option value="Closed">Closed</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-2 mt-2">
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 rounded-lg border text-sm text-gray-600">
                  Cancel
                </button>
                <button
                  onClick={handleCreateTicket}
                  disabled={!newTicket.ticket_key || !newTicket.title}
                  className="px-4 py-2 rounded-lg bg-black text-white text-sm disabled:opacity-40">
                  Create Ticket
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Dashboard>
  );
}
