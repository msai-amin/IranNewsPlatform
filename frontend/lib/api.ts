/**
 * API client for Iran News Wire backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Article {
  id: number;
  dedupe_hash: string;
  source_url: string | null;
  source_name: string | null;
  source_type: string | null;
  raw_persian_text: string | null;
  english_translation: string | null;
  fact_check_status: string | null;
  fact_check_notes: string[] | null;
  bias_score: number | null;
  final_copy: string | null;
  created_at: string | null;
  processed_at: string | null;
  // Corroboration fields
  story_group_id: string | null;
  is_primary: boolean | null;
  corroboration_count: number | null;
  corroborating_sources: string[] | null;
}

export interface CorroboratingSource {
  id: number;
  source_name: string | null;
  source_url: string | null;
  processed_at: string | null;
}

export interface ArticleListResponse {
  articles: Article[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface Stats {
  total: number;
  verified: number;
  unverified: number;
  propaganda: number;
  pending: number;
  by_source_type: Record<string, number>;
}

export interface PipelineRun {
  run_id: string;
  source_name: string | null;
  source_url: string | null;
  status: string;
  outcome: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
}

export interface PipelineRunsResponse {
  runs: PipelineRun[];
}

export interface PipelineStatsResponse {
  total_runs: number;
  by_status: Record<string, number>;
  by_outcome: Record<string, number>;
  last_run_at: string | null;
}

export interface PipelineNodeEvent {
  id: number;
  run_id: string;
  node_name: string;
  completed_at: string | null;
  status: string;
  log_message: string | null;
  source_name?: string | null;
}

export interface PipelineAgentsResponse {
  events: PipelineNodeEvent[];
}

export interface HealthResponse {
  status: string;
  database: boolean;
}

export interface FetchArticlesParams {
  page?: number;
  limit?: number;
  status?: string;
  source_type?: string;
  search?: string;
}

export async function fetchArticles(params: FetchArticlesParams = {}): Promise<ArticleListResponse> {
  const searchParams = new URLSearchParams();
  
  if (params.page) searchParams.set('page', params.page.toString());
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.status) searchParams.set('status', params.status);
  if (params.source_type) searchParams.set('source_type', params.source_type);
  if (params.search) searchParams.set('search', params.search);
  
  const url = `${API_BASE}/api/articles?${searchParams.toString()}`;
  const res = await fetch(url, { cache: 'no-store' });
  
  if (!res.ok) {
    throw new Error(`Failed to fetch articles: ${res.status}`);
  }
  
  return res.json();
}

export async function fetchArticle(id: number): Promise<Article> {
  const res = await fetch(`${API_BASE}/api/articles/${id}`, { cache: 'no-store' });
  
  if (!res.ok) {
    throw new Error(`Failed to fetch article: ${res.status}`);
  }
  
  return res.json();
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/api/stats`, { cache: 'no-store' });
  
  if (!res.ok) {
    throw new Error(`Failed to fetch stats: ${res.status}`);
  }
  
  return res.json();
}

export async function fetchCorroboratingSources(articleId: number): Promise<CorroboratingSource[]> {
  const res = await fetch(`${API_BASE}/api/articles/${articleId}/sources`, { cache: 'no-store' });
  
  if (!res.ok) {
    throw new Error(`Failed to fetch corroborating sources: ${res.status}`);
  }
  
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch health: ${res.status}`);
  }
  return res.json();
}

export interface FetchPipelineRunsParams {
  limit?: number;
  status?: string;
}

export async function fetchPipelineRuns(params: FetchPipelineRunsParams = {}): Promise<PipelineRunsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit != null) searchParams.set('limit', params.limit.toString());
  if (params.status) searchParams.set('status', params.status);
  const url = `${API_BASE}/api/pipeline/runs?${searchParams.toString()}`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch pipeline runs: ${res.status}`);
  }
  return res.json();
}

export async function fetchPipelineStats(): Promise<PipelineStatsResponse> {
  const res = await fetch(`${API_BASE}/api/pipeline/stats`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch pipeline stats: ${res.status}`);
  }
  return res.json();
}

export interface FetchPipelineAgentsParams {
  limit?: number;
  run_id?: string;
}

export async function fetchPipelineAgents(params: FetchPipelineAgentsParams = {}): Promise<PipelineAgentsResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit != null) searchParams.set('limit', params.limit.toString());
  if (params.run_id) searchParams.set('run_id', params.run_id);
  const url = `${API_BASE}/api/pipeline/agents?${searchParams.toString()}`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch pipeline agents: ${res.status}`);
  }
  return res.json();
}

/**
 * Extract headline from final_copy (first sentence or line)
 */
export function extractHeadline(finalCopy: string | null): string {
  if (!finalCopy) return 'Untitled Article';
  
  // Look for a bold headline pattern: **Headline**
  const boldMatch = finalCopy.match(/\*\*([^*]+)\*\*/);
  if (boldMatch) {
    return boldMatch[1].trim();
  }
  
  // Otherwise take first line or sentence
  const firstLine = finalCopy.split('\n')[0].trim();
  if (firstLine.length > 120) {
    return firstLine.substring(0, 117) + '...';
  }
  return firstLine;
}

/**
 * Extract preview text (first paragraph after headline)
 */
export function extractPreview(finalCopy: string | null, maxLength = 200): string {
  if (!finalCopy) return '';
  
  // Remove headline (bold text at start)
  let content = finalCopy.replace(/^\*\*[^*]+\*\*\s*/, '');
  
  // Get first substantial paragraph
  const paragraphs = content.split('\n\n').filter(p => p.trim().length > 20);
  const preview = paragraphs[0] || content.substring(0, maxLength);
  
  if (preview.length > maxLength) {
    return preview.substring(0, maxLength - 3) + '...';
  }
  return preview;
}
