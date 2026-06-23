export function SkeletonCard() {
  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5 animate-pulse">
      <div className="h-4 bg-surface-container-high rounded w-3/4 mb-3" />
      <div className="h-3 bg-surface-container-high rounded w-1/2 mb-2" />
      <div className="h-3 bg-surface-container-high rounded w-full" />
    </div>
  );
}

export function SkeletonImage({ aspect = 'aspect-[1.6]' }) {
  return (
    <div className={`bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden animate-pulse`}>
      <div className={`${aspect} bg-surface-container-high`} />
      <div className="p-4 space-y-2">
        <div className="h-4 bg-surface-container-high rounded w-2/3" />
        <div className="h-3 bg-surface-container-high rounded w-1/2" />
      </div>
    </div>
  );
}

export function SkeletonGrid({ count = 4, aspect = 'aspect-[1.6]' }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: count }, (_, i) => (
        <SkeletonImage key={i} aspect={aspect} />
      ))}
    </div>
  );
}

export function SkeletonRow({ rows = 3 }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex gap-4 p-4 bg-surface-container-lowest border border-outline-variant rounded-xl">
          <div className="w-10 h-10 bg-surface-container-high rounded-lg shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-surface-container-high rounded w-1/3" />
            <div className="h-3 bg-surface-container-high rounded w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SkeletonStats() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-pulse">
      {Array.from({ length: 4 }, (_, i) => (
        <div key={i} className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
          <div className="h-3 bg-surface-container-high rounded w-1/2 mb-3" />
          <div className="h-8 bg-surface-container-high rounded w-1/3" />
        </div>
      ))}
    </div>
  );
}
