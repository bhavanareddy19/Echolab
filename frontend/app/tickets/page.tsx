'use client';

import { Dashboard } from '@/components/Dashboard';
import Breadcrumb from '@/components/UI/Breadcrumb';
import { useEffect, useState, useRef } from 'react';
import {
  fetchTickets,
  createTicket,
  deleteTicket,
  uploadCSV,
  triggerAnalysis,
  TicketData,
  TicketsResponse,
} from '@/lib/api';

export default function TicketsPage() {
  const [tickets, setTickets] = useState<TicketData[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Create ticket form
  const [showCreate, setShowCreate] = useState(false);
  const [newTicket, setNewTicket] = useState({
    ticket_key: '',
    title: '',
    description: '',
    priority: 'Medium',
    status: 'Open',
    reporter: '',
    product: '',
    component: '',
  });
  const [creating, setCreating] = useState(false);

  // CSV upload
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  // Analysis
  const [analyzing, setAnalyzing] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    loadTickets();
  }, [page, filterPriority, filterStatus]);

  const loadTickets = () => {
    setLoading(true);
    fetchTickets({
      page,
      page_size: 20,
      priority: filterPriority || undefined,
      status: filterStatus || undefined,
      search: searchQuery || undefined,
    })
      .then((res: TicketsResponse) => {
        setTickets(res.tickets);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const handleSearch = () => {
    setPage(1);
    loadTickets();
  };

  const handleCreate = async () => {
    if (!newTicket.ticket_key.trim() || !newTicket.title.trim()) return;
    setCreating(true);
    try {
      const result = await createTicket({
        ticket_key: newTicket.ticket_key,
        title: newTicket.title,
        description: newTicket.description || undefined,
        priority: newTicket.priority,
        status: newTicket.status,
        reporter: newTicket.reporter || undefined,
        product: newTicket.product || undefined,
        component: newTicket.component || undefined,
      });
      setSuccess(`Ticket ${result.ticket_key} created successfully`);
      setNewTicket({ ticket_key: '', title: '', description: '', priority: 'Medium', status: 'Open', reporter: '', product: '', component: '' });
      setShowCreate(false);
      loadTickets();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create ticket';
      setError(message);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteTicket(id);
      setSuccess('Ticket deleted');
      loadTickets();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete';
      setError(message);
    }
  };

  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadCSV(file);
      setSuccess(`Uploaded ${result.inserted} tickets from ${result.filename}`);
      loadTickets();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      setError(message);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const result = await triggerAnalysis();
      setSuccess(result.message);
      loadTickets();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
    } finally {
      setAnalyzing(false);
    }
  };

  const getPriorityBadge = (priority: string | null) => {
    switch (priority?.toLowerCase()) {
      case 'critical': return 'bg-[#FFF2F2] text-[#F71111] border-[#FFDCDC]';
      case 'high': return 'bg-[#FFFBE3] text-[#F09800] border-[#FFE4B6]';
      case 'medium': return 'bg-[#F6FAFF] text-[#4652DC] border-[#D4E6FF]';
      case 'low': return 'bg-[#F6F6F6] text-[#7F7F7F] border-[#E8E8E8]';
      default: return 'bg-[#F6F6F6] text-[#7F7F7F] border-[#E8E8E8]';
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

        <div className="flex flex-row items-center justify-between">
          <div className="flex flex-col gap-2.5">
            <p className="font-semibold text-2xl tracking-[0.5%] leading-[26px] text-black">
              Tickets
            </p>
            <p className="font-medium text-sm tracking-[0.5%] leading-[16px] text-neutral-800">
              {total} total tickets
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="px-4 py-2.5 bg-[#E8E8E8] text-black rounded-lg text-sm font-medium hover:bg-[#d0d0d0] transition-colors disabled:opacity-50">
              {analyzing ? 'Analyzing...' : 'Run Analysis'}
            </button>
            <label className="px-4 py-2.5 bg-[#E8E8E8] text-black rounded-lg text-sm font-medium hover:bg-[#d0d0d0] transition-colors cursor-pointer">
              {uploading ? 'Uploading...' : 'Upload CSV'}
              <input
                ref={fileRef}
                type="file"
                accept=".csv"
                onChange={handleCSVUpload}
                className="hidden"
              />
            </label>
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="px-4 py-2.5 bg-[#5927FF] text-white rounded-lg text-sm font-medium hover:bg-[#4a1fd9] transition-colors">
              {showCreate ? 'Cancel' : '+ Add Ticket'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-600 text-sm">
            {error}
            <button onClick={() => setError(null)} className="ml-2 underline">Dismiss</button>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-green-700 text-sm">
            {success}
            <button onClick={() => setSuccess(null)} className="ml-2 underline">Dismiss</button>
          </div>
        )}

        {showCreate && (
          <div className="bg-primary p-4 rounded-xl flex flex-col gap-4 border border-[#E8E8E8]">
            <p className="font-semibold text-lg">Create New Ticket</p>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[#7F7F7F]">Ticket Key *</label>
                <input
                  value={newTicket.ticket_key}
                  onChange={(e) => setNewTicket({ ...newTicket, ticket_key: e.target.value })}
                  placeholder="e.g. ECHO-101"
                  className="border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[#7F7F7F]">Title *</label>
                <input
                  value={newTicket.title}
                  onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })}
                  placeholder="Brief summary of the issue"
                  className="border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]"
                />
              </div>
              <div className="flex flex-col gap-2 col-span-2">
                <label className="text-sm font-medium text-[#7F7F7F]">Description</label>
                <textarea
                  value={newTicket.description}
                  onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                  placeholder="Detailed description of the issue"
                  className="w-full border border-[#E8E8E8] rounded-lg p-3 text-sm min-h-[60px] resize-none focus:outline-none focus:border-[#5927FF]"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[#7F7F7F]">Priority</label>
                <select
                  value={newTicket.priority}
                  onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
                  className="border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]">
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[#7F7F7F]">Status</label>
                <select
                  value={newTicket.status}
                  onChange={(e) => setNewTicket({ ...newTicket, status: e.target.value })}
                  className="border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]">
                  <option value="Open">Open</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                  <option value="Closed">Closed</option>
                </select>
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[#7F7F7F]">Reporter</label>
                <input
                  value={newTicket.reporter}
                  onChange={(e) => setNewTicket({ ...newTicket, reporter: e.target.value })}
                  placeholder="Reporter name"
                  className="border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[#7F7F7F]">Product</label>
                <input
                  value={newTicket.product}
                  onChange={(e) => setNewTicket({ ...newTicket, product: e.target.value })}
                  placeholder="Product name"
                  className="border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]"
                />
              </div>
            </div>
            <button
              onClick={handleCreate}
              disabled={creating || !newTicket.ticket_key.trim() || !newTicket.title.trim()}
              className="self-end px-4 py-2.5 bg-[#5927FF] text-white rounded-lg text-sm font-medium hover:bg-[#4a1fd9] transition-colors disabled:opacity-50">
              {creating ? 'Creating...' : 'Create Ticket'}
            </button>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-3 items-center">
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search tickets..."
            className="flex-1 border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]"
          />
          <select
            value={filterPriority}
            onChange={(e) => { setFilterPriority(e.target.value); setPage(1); }}
            className="border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]">
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
          <select
            value={filterStatus}
            onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
            className="border border-[#E8E8E8] rounded-lg p-2.5 text-sm focus:outline-none focus:border-[#5927FF]">
            <option value="">All Statuses</option>
            <option value="Open">Open</option>
            <option value="In Progress">In Progress</option>
            <option value="Resolved">Resolved</option>
            <option value="Closed">Closed</option>
          </select>
          <button
            onClick={handleSearch}
            className="px-4 py-2.5 bg-[#E8E8E8] text-black rounded-lg text-sm font-medium hover:bg-[#d0d0d0] transition-colors">
            Search
          </button>
        </div>

        {/* Ticket table */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-pulse text-[#7F7F7F] text-sm">Loading tickets...</div>
          </div>
        ) : tickets.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <p className="text-[#7F7F7F] text-sm">No tickets found. Create a ticket or upload a CSV file.</p>
          </div>
        ) : (
          <>
            <div className="bg-white rounded-xl overflow-hidden border border-[#E8E8E8]">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[#F6F6F6] text-[#7F7F7F] text-left">
                    <th className="px-4 py-3 font-medium">Key</th>
                    <th className="px-4 py-3 font-medium">Title</th>
                    <th className="px-4 py-3 font-medium">Priority</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Type</th>
                    <th className="px-4 py-3 font-medium">Sentiment</th>
                    <th className="px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map((ticket) => (
                    <tr key={ticket.id} className="border-t border-[#E8E8E8] hover:bg-[#FAFAFA]">
                      <td className="px-4 py-3 font-medium text-[#5927FF]">
                        {ticket.ticket_key}
                      </td>
                      <td className="px-4 py-3 text-black max-w-[300px] truncate">
                        {ticket.title}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded border text-xs font-medium ${getPriorityBadge(ticket.priority)}`}>
                          {ticket.priority || 'N/A'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[#7F7F7F]">{ticket.status || 'N/A'}</td>
                      <td className="px-4 py-3 text-[#7F7F7F]">{ticket.feature_type || '—'}</td>
                      <td className="px-4 py-3 text-[#7F7F7F]">{ticket.sentiment || '—'}</td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleDelete(ticket.id)}
                          className="text-red-500 hover:text-red-700 text-xs">
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
              <p className="text-sm text-[#7F7F7F]">
                Page {page} of {totalPages} ({total} tickets)
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1.5 bg-[#E8E8E8] text-black rounded text-sm disabled:opacity-50">
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 bg-[#E8E8E8] text-black rounded text-sm disabled:opacity-50">
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </Dashboard>
  );
}
