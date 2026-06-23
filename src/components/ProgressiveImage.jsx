import { useState } from 'react';

// Blur-up progressive image loading (liblib-style)
export default function ProgressiveImage({ src, alt, className = '', containerClassName = '', aspectRatio }) {
  const [loaded, setLoaded] = useState(false);

  return (
    <div className={`relative overflow-hidden ${containerClassName}`} style={aspectRatio ? { aspectRatio } : {}}>
      {/* Blur placeholder */}
      {!loaded && (
        <div className="absolute inset-0 bg-surface-container animate-pulse" />
      )}
      {/* Actual image with blur-up transition */}
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        className={`${className} transition-all duration-500 ease-out ${loaded ? 'opacity-100 blur-0 scale-100' : 'opacity-0 blur-lg scale-105'}`}
        style={{ imageRendering: 'auto' }}
      />
    </div>
  );
}
