'use client';

import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { Radio, Globe, Clock, Users } from 'lucide-react';
import StatusBadge from './StatusBadge';
import { Article, extractHeadline, extractPreview } from '@/lib/api';

interface ArticleCardProps {
  article: Article;
  featured?: boolean;
}

export default function ArticleCard({ article, featured = false }: ArticleCardProps) {
  const headline = extractHeadline(article.final_copy);
  const preview = extractPreview(article.final_copy, featured ? 300 : 180);
  
  const timeAgo = article.processed_at 
    ? formatDistanceToNow(new Date(article.processed_at), { addSuffix: true })
    : 'Recently';
  
  const SourceIcon = article.source_type === 'telegram' ? Radio : Globe;
  
  // Estimate reading time (average 200 words per minute)
  const wordCount = article.final_copy?.split(/\s+/).length || 0;
  const readingTime = Math.max(1, Math.ceil(wordCount / 200));
  
  // Corroboration count (multiple sources reporting same story)
  const corroborationCount = article.corroboration_count || 1;
  const hasCorroboration = corroborationCount > 1;
  
  if (featured) {
    return (
      <Link href={`/article/${article.id}`}>
        <article className="bg-white rounded-2xl border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow duration-300">
          {/* Featured header bar */}
          <div className="bg-gray-900 px-6 py-2 flex items-center justify-between">
            <span className="text-xs font-medium text-white uppercase tracking-wider">Featured Story</span>
            {hasCorroboration && (
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-300">
                <Users className="w-3.5 h-3.5" />
                Reported by {corroborationCount} sources
              </span>
            )}
          </div>
          
          <div className="p-6 sm:p-8">
            {/* Meta row */}
            <div className="flex flex-wrap items-center gap-3 text-sm mb-4">
              <StatusBadge status={article.fact_check_status} size="md" />
              {hasCorroboration && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-medium border border-blue-200">
                  <Users className="w-3.5 h-3.5" />
                  {corroborationCount} sources
                </span>
              )}
              <span className="inline-flex items-center gap-1.5 text-gray-500">
                <SourceIcon className="w-4 h-4" />
                {article.source_name || 'Unknown'}
              </span>
              <span className="text-gray-300">•</span>
              <span className="text-gray-400">{timeAgo}</span>
            </div>
            
            {/* Headline */}
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4 leading-tight tracking-tight">
              {headline}
            </h2>
            
            {/* Preview */}
            <p className="text-gray-600 text-lg leading-relaxed mb-4">
              {preview}
            </p>
            
            {/* Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <span className="inline-flex items-center gap-1.5 text-sm text-gray-400">
                <Clock className="w-4 h-4" />
                {readingTime} min read
              </span>
              <span className="text-sm font-medium text-gray-900 hover:text-gray-600 transition-colors">
                Read full story →
              </span>
            </div>
          </div>
        </article>
      </Link>
    );
  }
  
  return (
    <Link href={`/article/${article.id}`}>
      <article className="group bg-white rounded-xl border border-gray-200 p-5 hover:border-gray-300 hover:shadow-md transition-all duration-200">
        {/* Meta row */}
        <div className="flex flex-wrap items-center gap-2 text-sm mb-3">
          <StatusBadge status={article.fact_check_status} />
          {hasCorroboration && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs font-medium border border-blue-200">
              <Users className="w-3 h-3" />
              {corroborationCount} sources
            </span>
          )}
          <span className="text-gray-300">•</span>
          <span className="inline-flex items-center gap-1 text-gray-500">
            <SourceIcon className="w-3.5 h-3.5" />
            {article.source_name || 'Unknown'}
          </span>
          <span className="text-gray-300">•</span>
          <span className="text-gray-400">{timeAgo}</span>
        </div>
        
        {/* Headline */}
        <h2 className="text-lg font-semibold text-gray-900 mb-2 leading-snug group-hover:text-gray-700 transition-colors">
          {headline}
        </h2>
        
        {/* Preview */}
        <p className="text-gray-600 text-sm leading-relaxed line-clamp-2 mb-3">
          {preview}
        </p>
        
        {/* Footer */}
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-1 text-xs text-gray-400">
            <Clock className="w-3.5 h-3.5" />
            {readingTime} min read
          </span>
          
          {/* Bias indicator (subtle) */}
          {article.bias_score !== null && article.bias_score > 5 && (
            <div className="flex items-center gap-1.5">
              <div className="h-1.5 w-12 bg-gray-100 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full ${
                    article.bias_score <= 3 ? 'bg-green-400' :
                    article.bias_score <= 6 ? 'bg-amber-400' : 'bg-red-400'
                  }`}
                  style={{ width: `${article.bias_score * 10}%` }}
                />
              </div>
              <span className="text-xs text-gray-400">bias</span>
            </div>
          )}
        </div>
      </article>
    </Link>
  );
}
