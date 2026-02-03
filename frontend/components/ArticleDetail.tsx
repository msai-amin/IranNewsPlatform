'use client';

import { useState } from 'react';
import { formatDistanceToNow, format } from 'date-fns';
import { 
  Radio, Globe, ExternalLink, ChevronDown, ChevronUp, 
  FileText, Languages, AlertCircle, Users, CheckCircle2 
} from 'lucide-react';
import StatusBadge from './StatusBadge';
import { Article } from '@/lib/api';

interface ArticleDetailProps {
  article: Article;
}

export default function ArticleDetail({ article }: ArticleDetailProps) {
  const [showTranslation, setShowTranslation] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [showSources, setShowSources] = useState(false);
  
  const timeAgo = article.processed_at 
    ? formatDistanceToNow(new Date(article.processed_at), { addSuffix: true })
    : null;
    
  const processedDate = article.processed_at
    ? format(new Date(article.processed_at), 'MMM d, yyyy h:mm a')
    : null;
  
  const SourceIcon = article.source_type === 'telegram' ? Radio : Globe;
  
  // Corroboration data
  const corroborationCount = article.corroboration_count || 1;
  const hasCorroboration = corroborationCount > 1;
  const corroboratingSources = article.corroborating_sources || [];
  
  // Parse final_copy to extract headline and body
  const finalCopy = article.final_copy || '';
  const headlineMatch = finalCopy.match(/^\*\*([^*]+)\*\*/);
  const headline = headlineMatch ? headlineMatch[1].trim() : null;
  const body = headlineMatch 
    ? finalCopy.replace(/^\*\*[^*]+\*\*\s*/, '').trim()
    : finalCopy;
  
  return (
    <article className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-gray-100">
        {/* Meta */}
        <div className="flex flex-wrap items-center gap-3 text-sm mb-4">
          <StatusBadge status={article.fact_check_status} size="md" />
          
          {hasCorroboration && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-medium border border-blue-200">
              <Users className="w-3.5 h-3.5" />
              Reported by {corroborationCount} sources
            </span>
          )}
          
          <span className="inline-flex items-center gap-1.5 text-gray-500">
            <SourceIcon className="w-4 h-4" />
            {article.source_name || 'Unknown source'}
          </span>
          
          {timeAgo && (
            <span className="text-gray-400" title={processedDate || ''}>
              {timeAgo}
            </span>
          )}
        </div>
        
        {/* Headline */}
        {headline && (
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight">
            {headline}
          </h1>
        )}
      </div>
      
      {/* Corroboration banner */}
      {hasCorroboration && (
        <div className="px-6 py-4 bg-blue-50 border-b border-blue-100">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-blue-900 mb-1">
                Cross-Source Corroboration
              </h3>
              <p className="text-sm text-blue-700">
                This story has been reported by {corroborationCount} independent sources, 
                increasing confidence in its accuracy.
              </p>
              {corroboratingSources.length > 0 && (
                <p className="text-xs text-blue-600 mt-1">
                  Also reported by: {corroboratingSources.join(', ')}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Bias score bar */}
      {article.bias_score !== null && (
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Bias Score</span>
            <span className="text-sm text-gray-500">{article.bias_score}/10</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all ${
                article.bias_score <= 3 ? 'bg-green-500' :
                article.bias_score <= 6 ? 'bg-amber-500' : 'bg-red-500'
              }`}
              style={{ width: `${article.bias_score * 10}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            {article.bias_score <= 3 && 'Low bias - appears balanced'}
            {article.bias_score > 3 && article.bias_score <= 6 && 'Moderate bias - some perspective present'}
            {article.bias_score > 6 && 'High bias - state-aligned perspective detected'}
          </p>
        </div>
      )}
      
      {/* Article body */}
      <div className="p-6">
        <div className="prose prose-gray max-w-none">
          {body.split('\n\n').map((paragraph, idx) => (
            <p key={idx} className="mb-4 text-gray-700 leading-relaxed">
              {paragraph}
            </p>
          ))}
        </div>
      </div>
      
      {/* Fact-check notes */}
      {article.fact_check_notes && article.fact_check_notes.length > 0 && (
        <div className="border-t border-gray-100">
          <button
            onClick={() => setShowNotes(!showNotes)}
            className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <span className="inline-flex items-center gap-2 font-medium text-gray-700">
              <AlertCircle className="w-4 h-4" />
              Fact-Check Notes ({article.fact_check_notes.length})
            </span>
            {showNotes ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          {showNotes && (
            <div className="px-6 pb-4">
              <ul className="space-y-2">
                {article.fact_check_notes.map((note, idx) => (
                  <li 
                    key={idx}
                    className="flex items-start gap-2 text-sm text-gray-600 bg-gray-50 rounded-lg p-3"
                  >
                    <span className="text-gray-400 mt-0.5">•</span>
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      
      {/* Translation toggle */}
      {article.english_translation && (
        <div className="border-t border-gray-100">
          <button
            onClick={() => setShowTranslation(!showTranslation)}
            className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
          >
            <span className="inline-flex items-center gap-2 font-medium text-gray-700">
              <Languages className="w-4 h-4" />
              Literal Translation
            </span>
            {showTranslation ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          {showTranslation && (
            <div className="px-6 pb-4">
              <div className="bg-blue-50 rounded-lg p-4 text-sm text-gray-700 leading-relaxed">
                {article.english_translation}
              </div>
              <p className="text-xs text-gray-400 mt-2">
                This is a literal translation preserving the original tone and word choices
              </p>
            </div>
          )}
        </div>
      )}
      
      {/* Source link */}
      {article.source_url && (
        <div className="px-6 py-4 border-t border-gray-100 bg-gray-50">
          <a
            href={article.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            View original source
          </a>
        </div>
      )}
    </article>
  );
}
