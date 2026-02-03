import Link from 'next/link';
import {
  fetchHealth,
  fetchPipelineRuns,
  fetchPipelineStats,
  fetchPipelineAgents,
} from '@/lib/api';
import { Activity, Database, Clock, CheckCircle, XCircle, Filter, ExternalLink, Terminal } from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import PipelineDiagram from '@/components/PipelineDiagram';

export const metadata = {
  title: 'Dev Dashboard | Iran Situation Room',
  description: 'Pipeline and agent monitoring',
};

async function HealthSection() {
  try {
    const health = await fetchHealth();
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">API</p>
              <p className="text-xs text-gray-500">
                {health.status === 'ok' ? 'Connected' : health.status}
              </p>
            </div>
            <div className="ml-auto">
              {health.status === 'ok' ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : (
                <XCircle className="w-5 h-5 text-red-500" />
              )}
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <Database className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Database</p>
              <p className="text-xs text-gray-500">
                {health.database ? 'Connected' : 'Disconnected'}
              </p>
            </div>
            <div className="ml-auto">
              {health.database ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : (
                <XCircle className="w-5 h-5 text-red-500" />
              )}
            </div>
          </div>
        </div>
      </div>
    );
  } catch (e) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-5 mb-8">
        <p className="text-sm font-medium text-red-800">Cannot reach API</p>
        <p className="text-xs text-red-600 mt-1">
          Ensure the backend is running on the URL set in NEXT_PUBLIC_API_URL (e.g. http://localhost:8000).
        </p>
      </div>
    );
  }
}

async function PipelineStatsSection() {
  try {
    const stats = await fetchPipelineStats();
    const lastRun = stats.last_run_at
      ? formatDistanceToNow(new Date(stats.last_run_at), { addSuffix: true })
      : 'Never';
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Stats</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          <div>
            <p className="text-2xl font-bold text-gray-900">{stats.total_runs}</p>
            <p className="text-xs text-gray-500">Total runs</p>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-700">Last run</p>
              <p className="text-xs text-gray-500">{lastRun}</p>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-4 text-sm">
          {Object.keys(stats.by_status).length > 0 && (
            <div>
              <span className="text-gray-500 font-medium">By status: </span>
              <span className="text-gray-700">
                {Object.entries(stats.by_status)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(', ')}
              </span>
            </div>
          )}
          {Object.keys(stats.by_outcome).length > 0 && (
            <div>
              <span className="text-gray-500 font-medium">By outcome: </span>
              <span className="text-gray-700">
                {Object.entries(stats.by_outcome)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(', ')}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  } catch (e) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 mb-8">
        <p className="text-sm font-medium text-amber-800">Pipeline stats unavailable</p>
      </div>
    );
  }
}

async function RecentRunsTable() {
  try {
    const { runs } = await fetchPipelineRuns({ limit: 50 });
    if (runs.length === 0) {
      return (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Filter className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No pipeline runs yet</h3>
          <p className="text-sm text-gray-500">
            Runs will appear here when the Telegram runner processes messages.
          </p>
        </div>
      );
    }
    return (
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Recent runs</h2>
          <Link
            href="/"
            className="text-sm font-medium text-gray-600 hover:text-gray-900 inline-flex items-center gap-1"
          >
            Open Iran Situation Room
            <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                <th className="text-left px-6 py-3 font-medium text-gray-600">Time</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Source</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Outcome</th>
                <th className="text-right px-6 py-3 font-medium text-gray-600">Duration</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Error</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.run_id} className="border-b border-gray-50 hover:bg-gray-50/50">
                  <td className="px-6 py-3 text-gray-700 whitespace-nowrap">
                    {run.started_at
                      ? format(new Date(run.started_at), 'MMM d, HH:mm:ss')
                      : '—'}
                  </td>
                  <td className="px-6 py-3 text-gray-700">
                    {run.source_name || '—'}
                  </td>
                  <td className="px-6 py-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        run.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : run.status === 'filtered'
                          ? 'bg-amber-100 text-amber-800'
                          : run.status === 'error'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {run.status}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-gray-600">{run.outcome || '—'}</td>
                  <td className="px-6 py-3 text-right text-gray-600">
                    {run.duration_ms != null ? `${run.duration_ms} ms` : '—'}
                  </td>
                  <td className="px-6 py-3 text-gray-600 max-w-xs truncate" title={run.error_message || ''}>
                    {run.error_message ? (
                      <span className="text-red-600" title={run.error_message}>
                        {run.error_message.length > 40
                          ? run.error_message.slice(0, 40) + '…'
                          : run.error_message}
                      </span>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  } catch (e) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
        <p className="text-sm font-medium text-amber-800">Recent runs unavailable</p>
      </div>
    );
  }
}

async function AgentsLogSection() {
  try {
    const { events } = await fetchPipelineAgents({ limit: 100 });
    if (events.length === 0) {
      return (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center mb-8">
          <Terminal className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Agents log</h2>
          <p className="text-sm text-gray-500">
            Agent activity will appear here when the pipeline processes messages.
          </p>
        </div>
      );
    }
    return (
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mb-8">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Agents log</h2>
          <p className="text-xs text-gray-500 mt-1">
            Per-node activity: scout, librarian, translator, analyst, editor
          </p>
        </div>
        <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Time</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Source</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Agent</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Log</th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                  <td className="px-6 py-2 text-gray-700 whitespace-nowrap">
                    {ev.completed_at ? format(new Date(ev.completed_at), 'HH:mm:ss.SSS') : '—'}
                  </td>
                  <td className="px-6 py-2 text-gray-600">{ev.source_name || '—'}</td>
                  <td className="px-6 py-2">
                    <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                      {ev.node_name}
                    </span>
                  </td>
                  <td className="px-6 py-2 text-gray-600 font-mono text-xs">
                    {ev.log_message || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  } catch (e) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 mb-8">
        <p className="text-sm font-medium text-amber-800">Agents log unavailable</p>
      </div>
    );
  }
}

export default function DashboardPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dev Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Monitor the pipeline and agent tasks. Data is recorded when the Telegram runner processes messages.
        </p>
      </div>

      <HealthSection />
      <div className="mb-8">
        <PipelineDiagram />
      </div>
      <PipelineStatsSection />
      <AgentsLogSection />
      <RecentRunsTable />
    </div>
  );
}
