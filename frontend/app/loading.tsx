export default function Loading() {
  return (
    <div className="space-y-6">
      {/* Stats skeleton */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-20 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
      
      {/* Filter skeleton */}
      <div className="h-16 bg-gray-100 rounded-xl animate-pulse" />
      
      {/* Article cards skeleton */}
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-20 h-5 bg-gray-100 rounded-full animate-pulse" />
              <div className="w-24 h-4 bg-gray-100 rounded animate-pulse" />
            </div>
            <div className="w-3/4 h-6 bg-gray-100 rounded animate-pulse mb-3" />
            <div className="space-y-2">
              <div className="w-full h-4 bg-gray-100 rounded animate-pulse" />
              <div className="w-5/6 h-4 bg-gray-100 rounded animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
