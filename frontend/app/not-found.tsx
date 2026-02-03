import Link from 'next/link';
import { Home } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Article Not Found</h2>
      <p className="text-gray-500 mb-6">
        The article you're looking for doesn't exist or has been removed.
      </p>
      <Link 
        href="/"
        className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
      >
        <Home className="w-4 h-4" />
        Go to homepage
      </Link>
    </div>
  );
}
