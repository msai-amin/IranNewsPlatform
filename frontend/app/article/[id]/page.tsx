import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import ArticleDetail from '@/components/ArticleDetail';
import { fetchArticle } from '@/lib/api';
import { notFound } from 'next/navigation';

interface ArticlePageProps {
  params: { id: string };
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const articleId = parseInt(params.id);
  
  if (isNaN(articleId)) {
    notFound();
  }
  
  try {
    const article = await fetchArticle(articleId);
    
    return (
      <>
        {/* Back button */}
        <Link 
          href="/"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to articles
        </Link>
        
        <ArticleDetail article={article} />
      </>
    );
  } catch (error) {
    notFound();
  }
}

export async function generateMetadata({ params }: ArticlePageProps) {
  try {
    const article = await fetchArticle(parseInt(params.id));
    const headline = article.final_copy?.match(/^\*\*([^*]+)\*\*/)?.[1] || 'Article';
    
    return {
      title: `${headline} | Iran News Wire`,
      description: article.final_copy?.substring(0, 160) || 'News article from Iran',
    };
  } catch {
    return {
      title: 'Article Not Found | Iran News Wire',
    };
  }
}
