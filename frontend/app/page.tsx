import { Suspense } from 'react';
import ArticleCard from '@/components/ArticleCard';
import FilterBar from '@/components/FilterBar';
import Pagination from '@/components/Pagination';
import { fetchArticles, fetchStats } from '@/lib/api';
import { CheckCircle, AlertCircle, AlertTriangle, Newspaper } from 'lucide-react';

interface HomeProps {
  searchParams: { 
    page?: string; 
    status?: string; 
    source_type?: string; 
    search?: string;
  };
}

async function StatsBar() {
  try {
    const stats = await fetchStats();
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <Newspaper className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              <p className="text-xs text-gray-500">Total Articles</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-green-200 p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-green-700">{stats.verified}</p>
              <p className="text-xs text-green-600">Verified</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-amber-200 p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center">
              <AlertCircle className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-amber-700">{stats.unverified}</p>
              <p className="text-xs text-amber-600">Unverified</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-red-200 p-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-700">{stats.propaganda}</p>
              <p className="text-xs text-red-600">Propaganda</p>
            </div>
          </div>
        </div>
      </div>
    );
  } catch (error) {
    return null;
  }
}

async function ArticleList({ searchParams }: HomeProps) {
  const page = parseInt(searchParams.page || '1');
  const hasFilters = searchParams.status || searchParams.source_type || searchParams.search;
  
  try {
    const data = await fetchArticles({
      page,
      limit: 20,
      status: searchParams.status,
      source_type: searchParams.source_type,
      search: searchParams.search,
    });
    
    if (data.articles.length === 0) {
      return (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Newspaper className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No articles found</h3>
          <p className="text-sm text-gray-500">
            {hasFilters
              ? 'Try adjusting your filters or search terms'
              : 'Articles will appear here as they are processed by the pipeline'}
          </p>
        </div>
      );
    }
    
    // Separate featured (first) article from the rest when not filtering
    const [featured, ...rest] = !hasFilters && page === 1 
      ? [data.articles[0], ...data.articles.slice(1)]
      : [null, ...data.articles];
    
    return (
      <>
        {/* Featured article (only on first page without filters) */}
        {featured && (
          <div className="mb-6">
            <ArticleCard article={featured} featured />
          </div>
        )}
        
        {/* Article grid */}
        {rest.length > 0 && (
          <>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                {hasFilters ? 'Filtered Results' : 'Latest News'}
              </h2>
              <span className="text-sm text-gray-400">{data.total} articles</span>
            </div>
            
            <div className="grid gap-4 sm:grid-cols-2">
              {rest.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </div>
          </>
        )}
        
        <Pagination 
          currentPage={data.page} 
          totalPages={data.total_pages}
          total={data.total}
        />
      </>
    );
  } catch (error) {
    return (
      <div className="bg-red-50 rounded-xl border border-red-200 p-8 text-center">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-8 h-8 text-red-500" />
        </div>
        <h3 className="text-lg font-medium text-red-700 mb-1">Failed to load articles</h3>
        <p className="text-sm text-red-500">
          Make sure the API server is running on port 8000
        </p>
      </div>
    );
  }
}

export default function Home({ searchParams }: HomeProps) {
  return (
    <>
      <Suspense fallback={
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 animate-pulse bg-gray-100 rounded-xl" />
          ))}
        </div>
      }>
        <StatsBar />
      </Suspense>
      
      <Suspense fallback={<div className="h-14 animate-pulse bg-gray-100 rounded-xl mb-6" />}>
        <FilterBar />
      </Suspense>
      
      <Suspense fallback={
        <div className="space-y-4">
          <div className="h-64 animate-pulse bg-gray-100 rounded-2xl mb-6" />
          <div className="grid gap-4 sm:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-40 animate-pulse bg-gray-100 rounded-xl" />
            ))}
          </div>
        </div>
      }>
        <ArticleList searchParams={searchParams} />
      </Suspense>
    </>
  );
}
