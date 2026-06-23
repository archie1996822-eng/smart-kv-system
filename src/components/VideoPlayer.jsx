import { useState, useRef, useCallback } from 'react';

function Icon({ name, filled = false, className = '' }) {
  return (<span className={`material-symbols-outlined ${className}`} style={filled ? { fontVariationSettings: '"FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24' } : {}}>{name}</span>);
}

export default function VideoPlayer({ src, title, poster, onClose }) {
  const videoRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);

  const formatTime = (t) => {
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const togglePlay = useCallback(() => {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) { v.play(); setPlaying(true); }
    else { v.pause(); setPlaying(false); }
  }, []);

  const handleTimeUpdate = () => {
    const v = videoRef.current;
    if (v) setCurrentTime(v.currentTime);
  };

  const handleLoaded = () => {
    const v = videoRef.current;
    if (v) setDuration(v.duration);
  };

  const handleSeek = (e) => {
    const v = videoRef.current;
    if (!v) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    v.currentTime = pct * duration;
  };

  const toggleMute = () => {
    const v = videoRef.current;
    if (!v) return;
    v.muted = !v.muted;
    setMuted(v.muted);
  };

  const handleVolume = (e) => {
    const v = videoRef.current;
    if (!v) return;
    const val = parseFloat(e.target.value);
    v.volume = val;
    setVolume(val);
    setMuted(val === 0);
  };

  return (
    <div className={`relative bg-black rounded-xl overflow-hidden group ${fullscreen ? 'fixed inset-0 z-[300]' : ''}`}>
      {/* Video element */}
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        className="w-full h-full object-contain"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoaded}
        onEnded={() => setPlaying(false)}
        onClick={togglePlay}
        playsInline
      />

      {/* Center play button overlay */}
      {!playing && (
        <div className="absolute inset-0 flex items-center justify-center cursor-pointer" onClick={togglePlay}>
          <div className="w-16 h-16 bg-white/90 rounded-full flex items-center justify-center hover:scale-110 transition-transform shadow-xl">
            <Icon name="play_arrow" className="text-4xl text-on-surface ml-1" />
          </div>
        </div>
      )}

      {/* Title bar */}
      {title && (
        <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/60 to-transparent">
          <h4 className="text-white text-sm font-semibold">{title}</h4>
        </div>
      )}

      {/* Close button */}
      {onClose && (
        <button onClick={onClose} className="absolute top-3 right-3 w-8 h-8 bg-black/50 rounded-full flex items-center justify-center text-white hover:bg-black/80 transition-colors z-10">
          <Icon name="close" className="text-lg" />
        </button>
      )}

      {/* Controls bar */}
      <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
        {/* Progress bar */}
        <div className="w-full h-1 bg-white/20 rounded-full mb-2 cursor-pointer" onClick={handleSeek}>
          <div className="h-full bg-primary rounded-full relative" style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}>
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow" />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={togglePlay} className="text-white hover:text-primary transition-colors">
              <Icon name={playing ? 'pause' : 'play_arrow'} className="text-2xl" />
            </button>
            <div className="flex items-center gap-2">
              <button onClick={toggleMute} className="text-white hover:text-primary transition-colors">
                <Icon name={muted || volume === 0 ? 'volume_off' : 'volume_up'} className="text-lg" />
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={muted ? 0 : volume}
                onChange={handleVolume}
                className="w-16 h-1 accent-primary"
              />
            </div>
            <span className="text-white text-xs font-jetbrains">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>
          <button onClick={() => { if (videoRef.current) videoRef.current.requestFullscreen().catch(() => {}); }} className="text-white hover:text-primary transition-colors">
            <Icon name="fullscreen" className="text-lg" />
          </button>
        </div>
      </div>
    </div>
  );
}
