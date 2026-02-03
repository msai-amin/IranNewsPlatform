'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Search, X } from 'lucide-react';

export default function FilterBar() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [status, setStatus] = useState(searchParams.get('status') || '');
  const [sourceType, setSourceType] = useState(searchParams.get('source_type') || '');
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [searchInput, setSearchInput] = useState(searchParams.get('search') || '');
  
  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);
  
  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (sourceType) params.set('source_type', sourceType);
    if (search) params.set('search', search);
    
    const queryString = params.toString();
    router.push(queryString ? `/?${queryString}` : '/');
  }, [status, sourceType, search, router]);
  
  const hasFilters = status || sourceType || search;
  
  const clearFilters = () => {
    setStatus('');
    setSourceType('');
    setSearch('');
    setSearchInput('');
  };
  
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search articles..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-shadow"
          />
        </div>
        
        {/* Filters */}
        <div className="flex gap-2">
          {/* Status filter */}
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="px-4 py-2.5 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent cursor-pointer transition-shadow min-w-[130px]"
          >
            <option value="">All Status</option>
            <option value="verified">✓ Verified</option>
            <option value="unverified">○ Unverified</option>
            <option value="propaganda">⚠ Propaganda</option>
          </select>
          
          {/* Source type filter */}
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className="px-4 py-2.5 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent cursor-pointer transition-shadow min-w-[130px]"
          >
            <option value="">All Sources</option>
            <option value="telegram">Telegram</option>
            <option value="web">Web</option>
          </select>
          
          {/* Clear filters */}
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="inline-flex items-center gap-1.5 px-3 py-2.5 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
              <span className="hidden sm:inline">Clear</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
