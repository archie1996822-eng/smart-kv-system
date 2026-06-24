import { useState, useRef } from 'react';
import Layout, { Icon, showToast, pushNotification } from '../components/Layout';
import VideoPlayer from '../components/VideoPlayer';
import { videoModels, videoTemplates, aspectRatios, generateScript, startVideoGen, pollVideoResult } from '../data/videoApi';
import { useShortcuts } from '../data/shortcuts';

function TabButton({ active, children, onClick }) {
  return (
    <button onClick={onClick} className={`px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${active ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container'}`}>
      {children}
    </button>
  );
}

export default function VideoStudio() {
  const [mode, setMode] = useState('text-to-video'); // text-to-video | image-to-video | my-videos
  const [prompt, setPrompt] = useState('');
  const [imageUrl, setImageUrl] = useState(null);
  const [selectedModel, setSelectedModel] = useState(videoModels[0].id);
  const [selectedRatio, setSelectedRatio] = useState('16:9');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [duration, setDuration] = useState(10);
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [videoResult, setVideoResult] = useState(null);
  const [script, setScript] = useState(null);
  const [generatingScript, setGeneratingScript] = useState(false);
  const [myVideos, setMyVideos] = useState([]);
  const fileRef = useRef(null);

  // Keyboard shortcuts
  useShortcuts({
    'Escape': () => { if (videoResult) setVideoResult(null); },
  });

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setImageUrl(ev.target.result);
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const handleGenerateScript = async () => {
    if (!prompt.trim()) { showToast('请先输入创作主题', 'error'); return; }
    setGeneratingScript(true);
    setStatusMsg('AI 正在生成视频脚本...');
    try {
      const s = await generateScript(prompt);
      setScript(s);
      setStatusMsg('脚本生成完成');
      showToast('AI 脚本已生成', 'success');
    } catch (err) {
      showToast('脚本生成失败: ' + err.message, 'error');
    }
    setGeneratingScript(false);
  };

  const handleGenerate = async () => {
    if (!prompt.trim() && !imageUrl) { showToast('请输入创作主题或上传图片', 'error'); return; }
    if (mode === 'image-to-video' && !imageUrl) { showToast('请先上传一张图片', 'error'); return; }

    setGenerating(true);
    setProgress(0);
    setVideoResult(null);
    setStatusMsg('提交视频生成任务...');

    try {
      const result = await startVideoGen({
        model: selectedModel,
        prompt: script ? `标题: ${script.title}\n风格: ${script.style}\n${script.scenes.map(s => `场景${s.scene}: ${s.description}`).join('\n')}` : prompt,
        imageUrl: mode === 'image-to-video' ? imageUrl : null,
        aspectRatio: selectedRatio,
        duration,
        template: selectedTemplate,
      });

      // Simulate progress for demo / poll for real
      setStatusMsg('视频生成中...');
      const interval = setInterval(() => {
        setProgress(p => {
          if (p >= 90) { clearInterval(interval); return 90; }
          return p + Math.random() * 15;
        });
      }, 2000);

      // Try real API polling
      let videoData;
      try {
        videoData = await pollVideoResult(result.id, 12);
        clearInterval(interval);
        setProgress(100);
      } catch {
        // Demo fallback: use a placeholder video
        clearInterval(interval);
        setProgress(100);
        videoData = {
          videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
          thumbnailUrl: imageUrl,
          duration: 10,
        };
        showToast('演示模式：使用示例视频', 'info');
      }

      setVideoResult(videoData);
      setMyVideos(prev => [{
        id: Date.now(),
        prompt: prompt.substring(0, 50),
        model: videoModels.find(m => m.id === selectedModel)?.name,
        thumbnailUrl: videoData.thumbnailUrl,
        videoUrl: videoData.videoUrl,
        createdAt: new Date().toLocaleString('zh-CN'),
      }, ...prev].slice(0, 20));

      setStatusMsg('✅ 视频生成完成');
      pushNotification('视频生成完成', prompt.substring(0, 30), 'play_circle', 'text-primary');
      showToast('视频生成完成！', 'success');
    } catch (err) {
      setStatusMsg('❌ 生成失败: ' + err.message);
      showToast('视频生成失败: ' + err.message, 'error');
    }
    setGenerating(false);
  };

  return (
    <Layout>
      <div className="p-4 md:p-8 max-w-[1440px] mx-auto">
        {/* Header */}
        <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
          <div>
            <h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface flex items-center gap-2">
              <Icon name="videocam" className="text-primary text-3xl" />视频创作工作室
            </h2>
            <p className="text-on-surface-variant mt-1">AI 驱动 · 文字/图片转视频 · 即梦式创作体验</p>
          </div>
          <div className="flex gap-2">
            <TabButton active={mode === 'text-to-video'} onClick={() => setMode('text-to-video')}>
              <Icon name="edit_note" className="text-[16px] mr-1 inline" />文生视频
            </TabButton>
            <TabButton active={mode === 'image-to-video'} onClick={() => setMode('image-to-video')}>
              <Icon name="image" className="text-[16px] mr-1 inline" />图生视频
            </TabButton>
            <TabButton active={mode === 'my-videos'} onClick={() => setMode('my-videos')}>
              <Icon name="playlist_play" className="text-[16px] mr-1 inline" />我的视频
            </TabButton>
          </div>
        </div>

        {statusMsg && (
          <div className="mb-4 px-4 py-2 bg-surface-container rounded-lg border border-outline-variant text-sm text-on-surface-variant font-jetbrains flex items-center gap-2">
            <Icon name="info" className="text-primary text-[18px]" />{statusMsg}
          </div>
        )}

        {/* Text-to-Video & Image-to-Video modes */}
        {mode !== 'my-videos' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main input area */}
            <div className="lg:col-span-2 space-y-4">
              {/* Prompt input */}
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
                <label className="text-sm font-semibold text-on-surface mb-3 block">
                  {mode === 'text-to-video' ? '创作主题 / 文案描述' : '动效描述（图片将作为首帧）'}
                </label>
                <textarea
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                  placeholder={mode === 'text-to-video'
                    ? '例如：一个科技感的产品发布会开场视频，蓝色调，粒子特效，快速切换的产品特写镜头...'
                    : '例如：这张图缓慢放大，光线从左到右扫过，Logo浮现在右上角，淡入淡出效果...'}
                  className="w-full px-4 py-3 bg-surface border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary outline-none transition-all text-sm resize-none"
                  rows={5}
                  disabled={generating}
                />
                <div className="flex gap-2 mt-3 flex-wrap">
                  <button onClick={handleGenerateScript} disabled={generatingScript || !prompt.trim()} className="px-4 py-2 border border-secondary text-secondary rounded-lg text-sm hover:bg-secondary/10 transition-all disabled:opacity-30 flex items-center gap-1">
                    <Icon name="auto_awesome" className="text-[16px]" />{generatingScript ? '生成中...' : 'AI 生成脚本'}
                  </button>
                  <span className="text-[10px] text-on-surface-variant flex items-center">{prompt.length} 字</span>
                </div>
              </div>

              {/* Image upload (for image-to-video mode) */}
              {mode === 'image-to-video' && (
                <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
                  <label className="text-sm font-semibold text-on-surface mb-3 block">上传起始图片</label>
                  {imageUrl ? (
                    <div className="relative inline-block group">
                      <img src={imageUrl} alt="起始图" className="max-h-40 rounded-lg border border-outline-variant" />
                      <button onClick={() => setImageUrl(null)} className="absolute top-1 right-1 bg-white/90 p-1 rounded-full shadow opacity-0 group-hover:opacity-100 transition-opacity">
                        <Icon name="close" className="text-sm text-error" />
                      </button>
                    </div>
                  ) : (
                    <div onClick={() => fileRef.current?.click()} className="border-2 border-dashed border-outline-variant rounded-xl p-8 text-center cursor-pointer hover:border-primary transition-colors">
                      <Icon name="cloud_upload" className="text-3xl text-outline-variant mb-2" />
                      <p className="text-sm text-on-surface-variant">点击上传图片</p>
                      <p className="text-[10px] text-outline">支持 JPG/PNG，建议 1080p+</p>
                    </div>
                  )}
                  <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleImageUpload} />
                </div>
              )}

              {/* AI Script preview */}
              {script && (
                <div className="bg-surface-container-lowest border border-secondary/30 rounded-xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-sm text-on-surface flex items-center gap-2">
                      <Icon name="description" className="text-secondary" />AI 脚本: {script.title}
                    </h4>
                    <span className="text-[10px] text-outline">预计 {script.duration}</span>
                  </div>
                  <div className="space-y-2">
                    {script.scenes?.map((s, i) => (
                      <div key={i} className="flex gap-3 p-2 rounded-lg hover:bg-surface-container transition-colors text-xs">
                        <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold shrink-0">{s.scene}</span>
                        <div className="flex-1">
                          <p className="text-on-surface font-medium">{s.description}</p>
                          <p className="text-on-surface-variant mt-0.5">🎬 {s.visual} | 💬 {s.text} | ⏱ {s.duration}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  {script.bgm && <p className="text-xs text-outline mt-3">🎵 推荐BGM: {script.bgm}</p>}
                </div>
              )}
            </div>

            {/* Sidebar: Settings */}
            <div className="space-y-4">
              {/* Model selector */}
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
                <h4 className="text-sm font-semibold text-on-surface mb-3">视频模型</h4>
                <div className="space-y-2">
                  {videoModels.map(m => (
                    <button key={m.id} onClick={() => setSelectedModel(m.id)} className={`w-full text-left p-3 rounded-lg border transition-all ${selectedModel === m.id ? 'border-primary bg-primary/5' : 'border-outline-variant hover:border-primary/50'}`}>
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-sm text-on-surface">{m.name}</span>
                        <span className="font-jetbrains text-[10px] text-primary">{m.price}</span>
                      </div>
                      <p className="text-[10px] text-on-surface-variant mt-1">{m.desc} · {m.duration}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Aspect ratio */}
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
                <h4 className="text-sm font-semibold text-on-surface mb-3">画面比例</h4>
                <div className="grid grid-cols-2 gap-2">
                  {aspectRatios.map(r => (
                    <button key={r.id} onClick={() => setSelectedRatio(r.id)} className={`p-2 rounded-lg border text-xs transition-all ${selectedRatio === r.id ? 'border-primary bg-primary/5 text-primary' : 'border-outline-variant text-on-surface-variant hover:border-primary/50'}`}>
                      <Icon name={r.icon} className="text-[16px] block mx-auto mb-1" />{r.label}<span className="block text-[9px] text-outline">{r.w}×{r.h}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Duration */}
              <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-5">
                <h4 className="text-sm font-semibold text-on-surface mb-3">时长: {duration}秒</h4>
                <input type="range" min="5" max="60" step="5" value={duration} onChange={e => setDuration(Number(e.target.value))} className="w-full accent-primary" />
                <div className="flex justify-between text-[10px] text-outline mt-1"><span>5秒</span><span>60秒</span></div>
              </div>

              {/* Generate button */}
              <button onClick={handleGenerate} disabled={generating || (!prompt.trim() && !imageUrl)} className="w-full py-4 bg-primary text-on-primary rounded-xl font-hanken text-lg font-bold hover:shadow-xl hover:shadow-primary/30 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                {generating ? (
                  <><span className="animate-spin"><Icon name="progress_activity" /></span>生成中 {Math.round(progress)}%</>
                ) : (
                  <><Icon name="auto_awesome" filled />开始生成视频</>
                )}
              </button>

              {/* Progress bar */}
              {generating && (
                <div className="w-full h-2 bg-surface-container-high rounded-full overflow-hidden">
                  <div className="h-full processing-bar transition-all duration-1000" style={{ width: `${progress}%` }} />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Video Templates */}
        {mode !== 'my-videos' && !generating && !videoResult && (
          <div className="mt-8">
            <h4 className="text-sm font-semibold text-on-surface mb-3">快速模板</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {videoTemplates.map(t => (
                <button key={t.id} onClick={() => { setSelectedTemplate(t.id); setPrompt(`使用"${t.name}"模板生成一个${t.desc}的视频`); }} className={`p-4 rounded-xl border text-center transition-all ${selectedTemplate === t.id ? 'border-primary bg-primary/5' : 'border-outline-variant hover:border-primary/50'}`}>
                  <Icon name={t.icon} className="text-2xl text-primary mb-2 block mx-auto" />
                  <p className="text-xs font-semibold text-on-surface">{t.name}</p>
                  <p className="text-[9px] text-on-surface-variant mt-1">{t.desc}</p>
                  <span className="text-[9px] text-primary mt-1 block">{t.duration}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Video result */}
        {videoResult && (
          <div className="mt-6 bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
            <div className="p-4 border-b border-outline-variant flex items-center justify-between">
              <h3 className="font-semibold text-on-surface">生成结果</h3>
              <button onClick={() => setVideoResult(null)} className="text-outline hover:text-error transition-colors">
                <Icon name="close" />
              </button>
            </div>
            <div className="max-w-4xl mx-auto p-4">
              <VideoPlayer src={videoResult.videoUrl} title={prompt.substring(0, 50)} poster={videoResult.thumbnailUrl} />
              <div className="flex gap-3 mt-4 justify-center">
                <button onClick={() => {
                  const a = document.createElement('a');
                  a.href = videoResult.videoUrl;
                  a.download = 'miketv-video.mp4';
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                }} className="px-6 py-2 bg-primary text-on-primary rounded-lg font-semibold hover:shadow flex items-center gap-2">
                  <Icon name="download" />下载视频
                </button>
                <button onClick={() => {
                  navigator.clipboard.writeText(videoResult.videoUrl);
                  showToast('视频链接已复制', 'success');
                }} className="px-6 py-2 border border-outline-variant rounded-lg text-sm hover:bg-surface-container flex items-center gap-2">
                  <Icon name="share" />分享链接
                </button>
              </div>
            </div>
          </div>
        )}

        {/* My Videos */}
        {mode === 'my-videos' && (
          <div>
            {myVideos.length === 0 ? (
              <div className="text-center py-20">
                <Icon name="videocam_off" className="text-6xl text-outline-variant mb-4" />
                <h3 className="text-xl font-semibold text-on-surface mb-2">还没有生成的视频</h3>
                <p className="text-on-surface-variant mb-4">切换到"文生视频"或"图生视频"开始创作</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {myVideos.map(v => (
                  <div key={v.id} className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden group cursor-pointer hover:border-primary/50 transition-all">
                    <div className="aspect-video bg-surface-container relative" onClick={() => setVideoResult(v)}>
                      {v.thumbnailUrl ? (
                        <img src={v.thumbnailUrl} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Icon name="play_circle" className="text-5xl text-outline-variant" />
                        </div>
                      )}
                      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                        <div className="w-12 h-12 bg-white/90 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                          <Icon name="play_arrow" className="text-2xl text-on-surface ml-0.5" />
                        </div>
                      </div>
                    </div>
                    <div className="p-3">
                      <p className="text-xs text-on-surface font-medium truncate">{v.prompt}</p>
                      <div className="flex justify-between mt-2">
                        <span className="text-[10px] text-outline">{v.model}</span>
                        <span className="text-[10px] text-outline">{v.createdAt}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}
