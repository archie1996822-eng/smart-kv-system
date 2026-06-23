import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import WebGLBackground from '../components/WebGLBackground';
import { getCurrentUser } from '../data/auth';
import { createPaymentSession } from '../data/payment';

// Load CMS data from admin console (or use defaults)
function loadCMS() {
  try {
    const v = localStorage.getItem('smart_kv_cms_homepage');
    return v ? JSON.parse(v) : null;
  } catch { return null; }
}

// ---- Image URLs (from stitch design) ----
const LOGO_URL = 'https://lh3.googleusercontent.com/aida/AP1WRLsNPccp36giEoc_6PlALv787M8OKGcgIfr-PafVPLfszyax9CoziE3QLkvX5-vWXiwjaLRc-r3fW1ushdVEAqL1h5oOqkXwL2ycjqkicO9PTc0ruKETW1oA-Fm2GuBbIIdKwxswCUJjlRztF5fgG6twziSN9Xewsnhh57WSkPPAgCH4qg9DW5r5J07Qq9TZo3hrR5vTpmdE3tQpmselwPOSTcpLlLH4aAE8M8enhe3bSDEE0-XsKUkxRJjt';

const MODEL_IMAGES = {
  seedance: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC1e1WSY3O1xhkDTlLhjTGo4VPjwElIvgVcd-_MT5e_GWzjGQWuyl-qAnldqyfHCg01njHqAKhWOUNRjJJW7AiDdFqSlJsmL9j9ksZUsDpt-gzDrBslS4r5eNxTClIBQhK94dDLJl8zpHiRC7TnsLdoKidFfziWJsqMsLXIxShSaD-lpEjEVzPvA_ukXypux5fpThNIOr5u_yXMvptJOt1hiqHu5VDgZ0zwKrqXLgSisnR-Zm1QbWNTWJCxsnYlmdQkhD_KvEMQ4Gae',
  seedanceMini: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDha-NVief6PuNralI-r-RwmWAxlBjXpK9qcMqmOCKCAFUF_DGzJPlnfLtaILFLZCZozLUorjM0C9a8z5uSbwi5HVCZQYxCMPkR481iCe82g8r6yWW2_P-QDLS-VyDvQnV-mzFe377uHpBduF-X7SJAbgAalRFSBgJ-MdG2KpbA586WvLP18KHmiOSB5P1WhWhLihPz200uoCiytqmpGXjaZsloBKR5ULvTcIKgZgqR0Nbldd3Xv6lKbr2z_UwcV6mg3cVAHOLuiw9J',
  gemini: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD-JlDH24VAeukSvTTRYGYMlo5hwxjrq3FQ626yje7MNok4KnkT-C1aOF9M4L-HFB_8kLwFsOHeMKdKkZzLCmSFhNzxpN0CVsi54552WuHlkIRtSUTM42C8o-hbNnLFHr7Qwk5EHastXFaAzPl-4egRXjQ9O9uzDJQFKYjUC9LvMPjr36SmfjUzHYemav2O1gU5VtFSrAOkFZZSnVmOVul5emc528PsWberi7bhHBmkPA9q6WTzeWEXKFzZmHZZuWh1H8sAxBhZtD8E',
  kling: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBxLBe7uK6rR-NKzOssOLJRTPoBWxZJrxBhblNTBZiMNvvuE4sxMab3E41ScNydnD7gJxZKJTU67X-CvoWn-3q7KuqcjpBjk9cnnho6jWHImzPKPwuSAQMLK4Cs8hKji06S_sPOmngSPJegb5N7zW3AzYrEmM6FmmIYpj1iLDX7gRoORvWEWYMaC22gSv1api3ninBN9GQ1d5vbTHbeRWAQdcAvFjzXVaw7eKluK4EampU9kGzvHqZLB5P3RFGohBGid7waM7e_EOlH',
  veo: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDPSBntZ7YfPfo6E4Z-Yl7VF1HeCIs9_3GEAP8NpGIxTMNPq7mDi7YPOQF0VAYlexNQ30egiDJUwrbzUxddJDA9C70v1vUIK356wYyFBN8msN9tDgoGOsPOMD-65zerbZoPbSd_EwxMeCVkzd7kISkMp8V-VBIaNnJv0Cd2KLommW4Fgq0DrCqook2mvDKfBiKkyZ0CNowo20wIs3VJJ1zIQ88IxMTJk32VUrCHhf7LU8lROvaXuLB31G-WelAnQfIDetLeS8fy1GSd',
  sora: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAcqBlFTXNnJKbZK7WpmmYtDuMRLIktp1cQ2-cXWQeAGE-Og-dLCJGAU2TUS1b0y-1NCm72hRJupoiRMSsFf6mrPrKK9cBu-L5XCEk6hO1Huwt5htpdhns5YJk3Zikf57Wr2i_BliP8O1be2T6BcvczwPpeFVCI7Us4zPVw7NgEIo3lIVuhoh5PABHT5bwEx0-qJLD57wbOItBCjQnmqJwUQR-3oofjQ4NnvwsYGshjmo3v387Plwpm1KNt4IoZ9rhDpWon-QCmLwvz',
};

const GALLERY_IMAGES = {
  col1: [
    { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBY40oaFTq1AX5JyV8PDk65cgt97s3OqAgCMd_mjsLUq7ArCfO1jty_LUDFxQ1DmHbNpOgQFSKCch9WruAawJvs5kj1sLt3YWWyUtAbe68kkNobqV6fa8NRjKswRcOCiOuOCytnQeU7oeqw6Lfi9d3t_sriqZS4vKQzvBiC6CTAlwB8cHh41wNM9XNw446WQOrTayDLV3cbdYQxzHDGz0CyLNsWVO0Gb0-XyGVN-K5AIuG07Jq8nzoxX--Ui31UBrLIw0Q0hKsYn_FG', title: '3D 抽象流体' },
    { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAnaEpdb8tRjkOI_hPqzVBKssZuqpbYuRvjd2o-FeIUysi1KACCRlV45_Sdxl9rxxQn8dwUu-nz1SXoK0rOTfGIEJzS-rO37_-S9NMbGpERR3IscprbbAl4Ts4q3beQyfVvT7mNAheBHT6Z5x9S7zh2aNUaqs72f6Fe6CUBWvObFyivoIqFuBTbtX6GZI0ERnNc_jgmZmD0ex1Sy8c4Hi_6SPZtoO-FPP3c314ujr7eUJrQDq-WSNMJI7LJGxkvdSXGOeyKTKDLiIy_', title: '复古科技感' },
    { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCsVfaG9eAeay1jL-Rp63jHc616RBDCjtkeT5QFqhaKx6ePn7pflYjWT0LTVC1iCtVRByloOM5vj9W_ANpib3xeuNYH1ceWeZVORnyH0cJk06k9EBhXtAcgV7zVUfWfjwAFJjAIJG2VADTCua2loMXL6q5Fx3UsCfXjMivCYQUpO_5c5eJb-WJDjrLkwtO7adohRbqSHDQ9VROZeTLBPGx6PnZpJEvlqnfbnxb0f9ZPFd59Vb8b-7nZhAHeV1lN8s75HFIrugkiN_v0', title: '几何渲染美学' },
  ],
  col2: [
    { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAmqmyK0Ea10N-g3APJM4ELjm2WWqCO7heND7wOrxp-DBPY16vxzr5D-D3AmMuH_qYzfJiDWf5IEbrfjkyuw1YiAI_nLaQRF_2DISVAQOXWVMUgxtD8c-Ho-40wdALmvZSuXSDQtesJTg5edNKFjsKDZqx_9CamZBh5G7FxXmroqVlLpEZUuwY0eZ6tG-ZSda7hODMRQ52mZxwVZ8iQKV-0rxniouLonMERf6Jw5bCjgFOuCwZBXwlmA2WsXlofV-OBeTv4Mqlv1GAQ', title: '波普艺术色彩' },
    { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuA_PP5-N9dmz4lbSe5p3JXUIZ5mO6g2q6xihCsnHe8UR6hpjpbIcgeKH1DHPnObaERkQ9j9p3yX_6QWedTMQ7f-xD8IJI3cssXQL0Ns1HEgU_wGLE33wZp9wedbSeAKiXIM4uvFb31F2_LzDbl1FQD3giiRiGH7kwk7sVxnZar1ce9842lcSNwltdesHKsIBe2mbsdj1jeLvprRbM8EXgRa-xCSFVKQ-jXo5qizFqceZtt59O5__25Cowo_GN3ZklNyeQTCJaBlfZrd', title: '全息渐变质感' },
    { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAgqq3OCBZhvi86w8HLEdxi1LLBLmeIluRPQtk6t7vzsOXVAetJbWB5UNf_8k83SNmrN19EnaYrxiwyBaxjgqeXA1C80LZDszEK_ofIkvbrRsAN8TsvnIMMwVTcZhP9fPVkDjO1m13yk_27awjaQrmyB4syzalZLrFa7GwlSFcof5j5I2HNprXs9W5ZEkiRSKVvtjfS6lZKTEJ657PBhL4E309nf9PzwvfzF8peffzgyx2vHogSMgk94C2zdILQ9wQ5PNdi-UtTuekB', title: '超现实主义材质' },
  ],
  col3: [
    { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCsFNl-j05OcHLpxp0mpchMBPAr7mCq6r95MGUER7iulJMBImdt-l6fNy4NxFV_xtVP8J_cBhNe52K1EQ6EVaWn8lGrCW6iLQZaQRl9QiDYzP6-R3eci7JdJuc9olofo1uYiePH28vPx7ik6L-j1d_ZFPZXjXTPRwDS2SVHdolPUQ4of9UzWXmcGSNghTnKtVVrxFIh-KMldxMIdAPSjlXNMaj6eHxxcLycHTJIje2YjSnwIQpF_zl_8fSL19FidimTvp846zhkT_Ka', title: '暗黑极简结构' },
    { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDs_wTEhzZAzzG8iVIyFSCb1QtsLu-tkfWgTRuk06Fxyraet7IpIG5MiXliiKUw9yJtD7TvXYO6Mhaee0uOXSb5VxG4UFEYp4t8Js3_Zg8qus1SSkCg9pBldlK6KX--hZX6LMiuxf6myQ3e77cgjJ365PWR-kAg6Xlezx6KJUvOcBotkRW-69-vZuLNnlt4Nqj6C9gXrmYQ83bULxHaYTDEaAYemyORLdEq3xatwcZf9n1mpkTaNT6SdpQlT3rsJW_zUv8uIBtfgLiS', title: '流体动力学模拟' },
    { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDBDdXJHpgfayeZzx-VsDDVny3wr9uMnrLiAdU-6hwfqs65GFTCUetnzJxP4qALuTtdgqS8-YKOWZ6EU0ko6brMkccBfi3WxZ54QSwpVvWnYopFdL55x_xthQnwk8FdgxKl1yse2ZoeYvM0V3l4qjY_cEaDpVYLIg6CyTsYd7cuhHiZWlOL6AbpJt3VKq57xhO-Nr8DVFvImNeVKHLeU-Y6XgY3Y9ceW8Hy1S--hWuah7HPkuMCnb4DQm37E-2IGnePVHyw8eJneSC_', title: '赛博霓虹光影' },
  ],
};

// ---- Model data ----
const MODELS = [
  { name: 'Seedance 2.0', desc: '视频生成', img: MODEL_IMAGES.seedance, glow: 'hover:shadow-[0_0_20px_rgba(255,78,124,0.3)]', border: 'hover:border-primary/50', gradient: 'from-primary/10' },
  { name: 'Seedance Mini', desc: '快速出图', img: MODEL_IMAGES.seedanceMini, glow: 'hover:shadow-[0_0_20px_rgba(235,178,255,0.3)]', border: 'hover:border-tertiary/50', gradient: 'from-tertiary/10' },
  { name: 'Gemini Omni', desc: '多模态大模型', img: MODEL_IMAGES.gemini, glow: 'hover:shadow-[0_0_20px_rgba(113,215,205,0.3)]', border: 'hover:border-secondary/50', gradient: 'from-secondary/10' },
  { name: 'Kling V3', desc: '高清视觉', img: MODEL_IMAGES.kling, glow: 'hover:shadow-[0_0_20px_rgba(255,78,124,0.3)]', border: 'hover:border-primary/50', gradient: 'from-primary/10' },
  { name: 'Veo 3.1', desc: '视频生成', img: MODEL_IMAGES.veo, glow: 'hover:shadow-[0_0_20px_rgba(235,178,255,0.3)]', border: 'hover:border-tertiary/50', gradient: 'from-tertiary/10' },
  { name: 'Sora 2', desc: '物理仿真', img: MODEL_IMAGES.sora, glow: 'hover:shadow-[0_0_20px_rgba(113,215,205,0.3)]', border: 'hover:border-secondary/50', gradient: 'from-secondary/10' },
];

const FEATURES = [
  { icon: 'design_services', title: '海报设计', desc: '专业模板一键生成，小白也能做出大牌感。', color: 'text-primary' },
  { icon: 'inventory_2', title: '周边物料', desc: '品牌周边、宣传册、文化衫等全品类物料设计。', color: 'text-tertiary' },
  { icon: 'description', title: '爆款脚本', desc: '深度洞察社交媒体热点，自动生成高转化脚本。', color: 'text-secondary' },
  { icon: 'movie_edit', title: '视频制作', desc: '智能剪辑与特效处理，快速产出高质量视频。', color: 'text-primary' },
  { icon: 'aspect_ratio', title: '无线画布', desc: '突破次元限制，在无限空间中自由排版与创作。', color: 'text-tertiary' },
  { icon: 'zoom_in', title: '图片放大', desc: 'AI超分技术，无损放大图片细节。', color: 'text-secondary' },
];

const NAV_LINKS = [
  { label: '功能', target: 'features' },
  { label: '模型', target: 'models' },
  { label: '探索', target: 'explore' },
  { label: '价格', target: 'pricing' },
  { label: '常见问题', target: 'faq' },
];

// ---- Gallery column component ----
function GalleryCol({ images, direction, className }) {
  const sets = [...images, ...images]; // duplicate for seamless scroll
  return (
    <div className={`flex-1 flex flex-col gap-4 md:gap-6 ${direction} ${className || ''}`}>
      {sets.map((img, i) => (
        <div
          key={i}
          className="rounded-2xl overflow-hidden glass-card-home group relative cursor-pointer border border-white/10 hover:border-primary/40 transition-all duration-300 shrink-0"
        >
          <img
            alt={img.title}
            className="w-full h-64 md:h-80 object-cover group-hover:scale-105 transition-transform duration-700"
            src={img.src}
            loading="lazy"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-transparent to-transparent opacity-80" />
          <div className="absolute bottom-0 left-0 p-4 w-full">
            <h3 className="text-on-surface text-sm font-bold">{img.title}</h3>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---- Main Home component ----
export default function Home() {
  const navigate = useNavigate();
  const [navSolid, setNavSolid] = useState(false);
  const loggedIn = !!getCurrentUser();
  const goToApp = () => navigate(loggedIn ? '/workbench' : '/login');

  // Load CMS overrides
  const cms = loadCMS();
  const heroTitle = cms?.hero?.title || '专为设计小白打造的 AI 爆款视频工具';
  const heroSubtitle = cms?.hero?.subtitle || '结合前沿 AI 模型与专业工作流，高效制作爆款视频。从 0 基础到爆款制造机，只需一键操作。';
  const heroCTA = cms?.hero?.cta || '立即开始创作';
  const cmsFeatures = cms?.features || FEATURES;
  const cmsPricing = cms?.pricing || null;
  const cmsFAQ = cms?.faq || null;

  // Navbar scroll effect
  useEffect(() => {
    const handleScroll = () => {
      setNavSolid(window.scrollY > 80);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Fade-in animation via IntersectionObserver
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.1 }
    );

    const elements = document.querySelectorAll('.fade-in');
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  // Smooth scroll to section (avoids HashRouter conflicts)
  const scrollTo = useCallback((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  return (
    <div className="home-dark min-h-screen bg-background text-on-surface overflow-x-hidden" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* ---- WebGL Background ---- */}
      <WebGLBackground />

      {/* ---- Top Navigation ---- */}
      <nav
        className={`fixed top-0 w-full z-50 border-b border-white/10 transition-all duration-300 ${
          navSolid ? 'home-nav-solid' : 'home-nav-glass'
        }`}
      >
        <div className="flex justify-between items-center h-20 px-4 md:px-10 max-w-[1280px] mx-auto">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <img alt="Miketv Logo" className="h-10 w-10" src={LOGO_URL} />
            <span className="text-2xl md:text-[32px] font-bold text-primary" style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600 }}>
              Miketv
            </span>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex gap-8 items-center">
            {NAV_LINKS.map((link) => (
              <button
                key={link.target}
                onClick={() => scrollTo(link.target)}
                className="text-on-surface-variant hover:text-primary transition-colors duration-300 text-base bg-transparent border-none cursor-pointer"
              >
                {link.label}
              </button>
            ))}
            <div className="h-4 w-px bg-white/20" />
            <button className="text-on-surface-variant hover:text-primary transition-colors duration-300 text-sm bg-transparent border-none cursor-pointer">
              中/EN
            </button>
            <button
              onClick={() => goToApp()}
              className="text-on-surface hover:text-primary transition-colors duration-300 text-sm bg-transparent border-none cursor-pointer"
            >
              登录
            </button>
            <button
              onClick={() => goToApp()}
              className="bg-primary-container text-on-primary-container text-sm px-6 py-2 rounded-full border border-primary hover:shadow-[0_0_15px_rgba(255,78,124,0.5)] transition-all duration-200 active:scale-95 cursor-pointer"
            >
              注册
            </button>
          </div>
        </div>
      </nav>

      {/* ---- Hero Section ---- */}
      <section className="relative pt-40 pb-20 px-4 md:px-10 min-h-screen flex items-center">
        <div className="max-w-[1280px] mx-auto w-full text-center fade-in">
          <img
            alt="Miketv Logo"
            className="h-24 md:h-32 w-auto mx-auto mb-8 animate-float"
            src={LOGO_URL}
          />
          <h1
            className="text-[48px] leading-tight mb-6 text-transparent bg-clip-text bg-gradient-to-r from-primary via-tertiary to-secondary"
            style={{ fontFamily: "'Inter', sans-serif", fontWeight: 700, letterSpacing: '-0.02em' }}
          >
            {heroTitle}
          </h1>
          <p
            className="text-base text-on-surface-variant max-w-[672px] mx-auto mb-10"
            style={{ lineHeight: 1.6 }}
          >
            {heroSubtitle}
          </p>
          <button
            onClick={() => goToApp()}
            className="bg-primary-container text-on-primary-container text-sm px-10 py-4 rounded-full border border-primary text-lg glow-hover-home transition-all duration-300 active:scale-95 mb-16 cursor-pointer"
          >
            {heroCTA}
          </button>
          {loggedIn && (
            <p className="text-xs text-on-surface-variant mt-2">
              已登录 · <button onClick={() => navigate('/app')} className="text-primary hover:underline">进入工作台</button>
            </p>
          )}

          {/* Video Player Mockup */}
          <div className="relative max-w-4xl mx-auto rounded-xl overflow-hidden glass-card-home border border-white/20 shadow-[0_20px_60px_rgba(233,30,99,0.2)] group cursor-pointer aspect-[16/9] flex items-center justify-center fade-in">
            <div
              className="absolute inset-0 bg-cover bg-center opacity-40 transition-opacity duration-500 group-hover:opacity-60"
              style={{ backgroundImage: `url('https://images.unsplash.com/photo-1536240478700-b869070f9279?auto=format&fit=crop&q=80')` }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-transparent to-transparent" />

            {/* Play Button */}
            <div className="relative z-10 w-20 h-20 bg-primary/90 rounded-full flex items-center justify-center play-btn-pulse backdrop-blur-md border border-white/30 group-hover:scale-110 transition-transform duration-300">
              <span className="material-symbols-outlined text-4xl text-on-primary ml-1">play_arrow</span>
            </div>

            {/* Player Controls Mockup */}
            <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 flex flex-col gap-2 z-10">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-primary" style={{ fontFamily: "'JetBrains Mono', monospace" }}>Miketv AI 生成中...</span>
                <span className="text-xs text-on-surface-variant" style={{ fontFamily: "'JetBrains Mono', monospace" }}>00:00 / 00:30</span>
              </div>
              <div className="w-full h-1.5 bg-surface/50 rounded-full overflow-hidden">
                <div className="w-1/3 h-full bg-gradient-to-r from-primary to-tertiary relative">
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg" />
                </div>
              </div>
              <div className="flex justify-between items-center mt-2">
                <div className="flex gap-4">
                  <span className="material-symbols-outlined text-on-surface hover:text-primary transition-colors text-xl">volume_up</span>
                  <span className="material-symbols-outlined text-on-surface hover:text-primary transition-colors text-xl">closed_caption</span>
                </div>
                <span className="material-symbols-outlined text-on-surface hover:text-primary transition-colors text-xl">fullscreen</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---- Features Section ---- */}
      <section className="py-24 px-4 md:px-10" id="features">
        <div className="max-w-[1280px] mx-auto">
          <h2
            className="text-[32px] text-center mb-16 fade-in"
            style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, lineHeight: 1.3 }}
          >
            核心能力，重塑视频生产
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cmsFeatures.map((f, i) => (
              <div
                key={f.title}
                className="glass-card-home p-8 rounded-2xl fade-in hover:-translate-y-2 transition-transform duration-300"
                style={{ transitionDelay: `${i * 100}ms` }}
              >
                <span
                  className={`material-symbols-outlined text-4xl ${f.color} mb-4`}
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  {f.icon}
                </span>
                <h3
                  className="text-2xl mb-3 text-secondary"
                  style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600 }}
                >
                  {f.title}
                </h3>
                <p className="text-on-surface-variant">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- AI Models Section ---- */}
      <section className="py-24 px-4 md:px-10 bg-surface-container-lowest/30 relative border-y border-white/5" id="models">
        <div className="max-w-[1280px] mx-auto">
          <div className="text-center mb-16 fade-in">
            <h2
              className="text-[32px] inline-flex items-center gap-3"
              style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, lineHeight: 1.3 }}
            >
              所有 <span className="text-transparent bg-clip-text bg-gradient-to-r from-tertiary to-secondary font-bold">领先的</span> AI 模型
            </h2>
            <p className="text-on-surface-variant mt-4 max-w-[672px] mx-auto">
              集成全球顶尖 AI 模型，提供最强大的视觉生成能力
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 fade-in">
            {MODELS.map((m, i) => (
              <div
                key={m.name}
                className={`glass-card-home rounded-xl p-4 text-center ${m.glow} transition-all duration-300 group cursor-pointer border border-white/10 ${m.border} relative overflow-hidden`}
                style={{ transitionDelay: `${i * 50}ms` }}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${m.gradient} to-transparent opacity-0 group-hover:opacity-100 transition-opacity`} />
                <div className="w-16 h-16 mx-auto mb-3 rounded-lg overflow-hidden bg-surface flex items-center justify-center p-2 border border-white/5">
                  <img alt={m.name} className="w-full h-full object-contain" src={m.img} loading="lazy" />
                </div>
                <h4 className="text-sm font-bold text-on-surface group-hover:text-primary transition-colors">{m.name}</h4>
                <p className="text-xs text-on-surface-variant mt-1">{m.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- Audience / Value Prop ---- */}
      <section className="py-24 bg-surface-container-low px-4 md:px-10 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/10 via-background to-background pointer-events-none" />
        <div className="max-w-[1280px] mx-auto relative z-10">
          <h2
            className="text-[32px] text-center mb-16 fade-in"
            style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, lineHeight: 1.3 }}
          >
            赋能每一位生态参与者
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: 'storefront', title: '电商卖家', desc: '告别高昂外包成本，海量低成本测试素材，快速测品打爆。', color: 'text-primary', border: 'border-primary/30', shadow: 'shadow-[0_0_15px_rgba(255,178,190,0.2)]' },
              { icon: 'videocam', title: '内容创作者', desc: '突破创作瓶颈，AI 辅助生成无限创意，轻松维持高频更新。', color: 'text-tertiary', border: 'border-tertiary/30', shadow: 'shadow-[0_0_15px_rgba(235,178,255,0.2)]' },
              { icon: 'campaign', title: '出海品牌', desc: '矩阵化铺设本地化内容，抢占社媒声量，建立品牌信任。', color: 'text-secondary', border: 'border-secondary/30', shadow: 'shadow-[0_0_15px_rgba(113,215,205,0.2)]' },
            ].map((item, i) => (
              <div key={item.title} className="text-center fade-in" style={{ transitionDelay: `${i * 150}ms` }}>
                <div className={`w-20 h-20 mx-auto rounded-full bg-surface-container-high flex items-center justify-center mb-6 border ${item.border} ${item.shadow}`}>
                  <span className={`material-symbols-outlined text-3xl ${item.color}`}>{item.icon}</span>
                </div>
                <h4
                  className="text-2xl mb-2"
                  style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600 }}
                >
                  {item.title}
                </h4>
                <p className="text-on-surface-variant text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- Design Exploration Gallery ---- */}
      <section className="py-24 px-4 md:px-10 bg-surface-dim relative overflow-hidden" id="explore">
        <div className="max-w-[1280px] mx-auto">
          <div className="text-center mb-16 fade-in">
            <h2
              className="text-[32px] inline-flex items-center gap-3"
              style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, lineHeight: 1.3 }}
            >
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-tertiary font-bold">Miketv</span> 设计探索
            </h2>
            <p className="text-on-surface-variant mt-4">海量优质 AI 设计案例，激发无限创作灵感</p>
          </div>

          {/* Interleaved Scrolling Grid */}
          <div className="relative h-[600px] md:h-[800px] overflow-hidden flex gap-4 md:gap-6 mx-auto mask-fade-y fade-in">
            <GalleryCol images={GALLERY_IMAGES.col1} direction="scroll-col-up" />
            <GalleryCol images={GALLERY_IMAGES.col2} direction="scroll-col-down" />
            <GalleryCol images={GALLERY_IMAGES.col3} direction="scroll-col-up-fast" className="hidden md:flex" />
          </div>

          <div className="text-center mt-12 relative z-10">
            <button className="text-primary hover:text-primary-fixed border border-primary/50 hover:bg-primary/10 px-8 py-3 rounded-full transition-all duration-300 text-sm font-medium bg-transparent cursor-pointer">
              探索更多精选案例
            </button>
          </div>
        </div>
      </section>

      {/* ---- Pricing Section ---- */}
      <section className="py-24 bg-surface-container-low px-4 md:px-10" id="pricing">
        <div className="max-w-[1280px] mx-auto">
          <h2 className="text-[32px] text-center mb-16 fade-in" style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, lineHeight: 1.3 }}>
            灵活定价，按需选择
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {(cmsPricing || [
              { name: '体验版', price: '免费', unit: '', desc: '适合个人体验', features: ['每月 10 次生成', '基础视觉分析', '标准物料模板', '3 天历史记录'], cta: '免费体验', highlight: false },
              { name: '专业版', price: '¥99', unit: '/月', desc: '适合独立设计师', features: ['每月 200 次生成', 'Gemini 2.5 Pro 分析', '全部物料类型', '30 天历史记录', '品牌资产管理', '模板保存与加载'], cta: '立即订阅', highlight: true },
              { name: '企业版', price: '¥399', unit: '/月', desc: '适合设计团队', features: ['无限次生成', '全部 AI 模型', '团队协作与审批', 'API 接口对接', '专属客服支持', '定制物料开发'], cta: '联系销售', highlight: false },
            ]).map((plan, i) => (
              <div key={plan.name} className={`fade-in rounded-2xl p-8 flex flex-col ${plan.highlight ? 'bg-primary-container/10 border-2 border-primary shadow-[0_0_30px_rgba(255,78,124,0.15)] relative' : 'glass-card-home border border-white/10'}`} style={{ transitionDelay: `${i * 150}ms` }}>
                {plan.highlight && <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-on-primary text-xs font-semibold px-4 py-1 rounded-full">最受欢迎</div>}
                <h3 className="text-xl font-bold text-on-surface mb-1">{plan.name}</h3>
                <p className="text-xs text-on-surface-variant mb-4">{plan.desc}</p>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-on-surface">{plan.price}</span>
                  <span className="text-on-surface-variant text-sm">{plan.unit}</span>
                </div>
                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map(f => (
                    <li key={f} className="flex items-center gap-2 text-sm text-on-surface-variant">
                      <span className="material-symbols-outlined text-secondary text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                      {f}
                    </li>
                  ))}
                </ul>
                <button onClick={() => {
                  if (plan.name === '体验版') { goToApp(); return; }
                  if (!loggedIn) { navigate('/login'); return; }
                  const session = createPaymentSession(plan.name === '专业版' ? 'pro' : 'enterprise', getCurrentUser()?.username);
                  navigate('/app');
                }} className={`w-full py-3 rounded-full font-semibold text-sm transition-all active:scale-95 cursor-pointer ${plan.highlight ? 'bg-primary text-on-primary hover:shadow-lg' : 'border border-primary text-primary hover:bg-primary/10'}`}>
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- FAQ Section ---- */}
      <section className="py-24 bg-surface-container-low px-4 md:px-10" id="faq">
        <div className="max-w-3xl mx-auto">
          <h2
            className="text-[32px] text-center mb-16 fade-in"
            style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, lineHeight: 1.3 }}
          >
            常见问题
          </h2>
          <div className="space-y-4">
            {(cmsFAQ || [
              { q: '生成一条视频需要多长时间？', a: '通常在 1-3 分钟内即可完成高质量视频的渲染与生成，具体取决于您选择的素材复杂度和生成时长。' },
              { q: '自动去重功能能保证100%通过审核吗？', a: '我们的算法深度处理视频帧、音频和特效，极大提升了原创通过率，能有效规避大多数平台的机器查重。' },
            ]).map((faq, i) => (
              <div
                key={i}
                className="glass-card-home p-6 rounded-2xl fade-in"
                style={{ transitionDelay: `${i * 200}ms` }}
              >
                <h4 className="text-sm font-medium text-primary mb-2">{faq.q}</h4>
                <p className="text-on-surface-variant text-sm">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- Footer ---- */}
      <footer className="bg-surface-container-lowest w-full py-12 px-4 md:px-10 border-t border-white/5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-[1280px] mx-auto items-center">
          <div className="text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
              <img alt="Miketv Logo" className="h-6 w-6" src={LOGO_URL} />
              <span
                className="text-xl font-black text-on-surface"
                style={{ fontFamily: "'Inter', sans-serif" }}
              >
                Miketv
              </span>
            </div>
            <p className="text-sm text-on-surface-variant mt-2">
              © 2024 Miketv AI视频创作平台. All rights reserved.
            </p>
            <p className="text-sm text-primary mt-2">
              客服联系方式：微信/电话 138-xxxx-xxxx
            </p>
          </div>
          <div className="flex justify-center md:justify-end gap-6 mt-6 md:mt-0">
            {[
              { label: '隐私政策', action: () => scrollTo('faq') },
              { label: '服务条款', action: () => scrollTo('pricing') },
              { label: '联系我们', action: () => scrollTo('faq') },
              { label: '关于我们', action: () => scrollTo('features') },
            ].map((item) => (
              <button
                key={item.label}
                onClick={item.action}
                className="text-sm text-on-surface-variant hover:text-secondary transition-opacity opacity-80 hover:opacity-100 bg-transparent border-none cursor-pointer"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
