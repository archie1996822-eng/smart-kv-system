import { useState, useEffect } from 'react';
import Layout, { Icon } from '../components/Layout';

const GALLERY = [
  { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBY40oaFTq1AX5JyV8PDk65cgt97s3OqAgCMd_mjsLUq7ArCfO1jty_LUDFxQ1DmHbNpOgQFSKCch9WruAawJvs5kj1sLt3YWWyUtAbe68kkNobqV6fa8NRjKswRcOCiOuOCytnQeU7oeqw6Lfi9d3t_sriqZS4vKQzvBiC6CTAlwB8cHh41wNM9XNw446WQOrTayDLV3cbdYQxzHDGz0CyLNsWVO0Gb0-XyGVN-K5AIuG07Jq8nzoxX--Ui31UBrLIw0Q0hKsYn_FG', title: '3D 抽象流体', cat: '抽象艺术' },
  { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAnaEpdb8tRjkOI_hPqzVBKssZuqpbYuRvjd2o-FeIUysi1KACCRlV45_Sdxl9rxxQn8dwUu-nz1SXoK0rOTfGIEJzS-rO37_-S9NMbGpERR3IscprbbAl4Ts4q3beQyfVvT7mNAheBHT6Z5x9S7zh2aNUaqs72f6Fe6CUBWvObFyivoIqFuBTbtX6GZI0ERnNc_jgmZmD0ex1Sy8c4Hi_6SPZtoO-FPP3c314ujr7eUJrQDq-WSNMJI7LJGxkvdSXGOeyKTKDLiIy_', title: '复古科技感', cat: '科技' },
  { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCsVfaG9eAeay1jL-Rp63jHc616RBDCjtkeT5QFqhaKx6ePn7pflYjWT0LTVC1iCtVRByloOM5vj9W_ANpib3xeuNYH1ceWeZVORnyH0cJk06k9EBhXtAcgV7zVUfWfjwAFJjAIJG2VADTCua2loMXL6q5Fx3UsCfXjMivCYQUpO_5c5eJb-WJDjrLkwtO7adohRbqSHDQ9VROZeTLBPGx6PnZpJEvlqnfbnxb0f9ZPFd59Vb8b-7nZhAHeV1lN8s75HFIrugkiN_v0', title: '几何渲染美学', cat: '设计' },
  { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAmqmyK0Ea10N-g3APJM4ELjm2WWqCO7heND7wOrxp-DBPY16vxzr5D-D3AmMuH_qYzfJiDWf5IEbrfjkyuw1YiAI_nLaQRF_2DISVAQOXWVMUgxtD8c-Ho-40wdALmvZSuXSDQtesJTg5edNKFjsKDZqx_9CamZBh5G7FxXmroqVlLpEZUuwY0eZ6tG-ZSda7hODMRQ52mZxwVZ8iQKV-0rxniouLonMERf6Jw5bCjgFOuCwZBXwlmA2WsXlofV-OBeTv4Mqlv1GAQ', title: '波普艺术色彩', cat: '色彩' },
  { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuA_PP5-N9dmz4lbSe5p3JXUIZ5mO6g2q6xihCsnHe8UR6hpjpbIcgeKH1DHPnObaERkQ9j9p3yX_6QWedTMQ7f-xD8IJI3cssXQL0Ns1HEgU_wGLE33wZp9wedbSeAKiXIM4uvFb31F2_LzDbl1FQD3giiRiGH7kwk7sVxnZar1ce9842lcSNwltdesHKsIBe2mbsdj1jeLvprRbM8EXgRa-xCSFVKQ-jXo5qizFqceZtt59O5__25Cowo_GN3ZklNyeQTCJaBlfZrd', title: '全息渐变质感', cat: '色彩' },
  { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAgqq3OCBZhvi86w8HLEdxi1LLBLmeIluRPQtk6t7vzsOXVAetJbWB5UNf_8k83SNmrN19EnaYrxiwyBaxjgqeXA1C80LZDszEK_ofIkvbrRsAN8TsvnIMMwVTcZhP9fPVkDjO1m13yk_27awjaQrmyB4syzalZLrFa7GwlSFcof5j5I2HNprXs9W5ZEkiRSKVvtjfS6lZKTEJ657PBhL4E309nf9PzwvfzF8peffzgyx2vHogSMgk94C2zdILQ9wQ5PNdi-UtTuekB', title: '超现实主义材质', cat: '抽象艺术' },
  { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCsFNl-j05OcHLpxp0mpchMBPAr7mCq6r95MGUER7iulJMBImdt-l6fNy4NxFV_xtVP8J_cBhNe52K1EQ6EVaWn8lGrCW6iLQZaQRl9QiDYzP6-R3eci7JdJuc9olofo1uYiePH28vPx7ik6L-j1d_ZFPZXjXTPRwDS2SVHdolPUQ4of9UzWXmcGSNghTnKtVVrxFIh-KMldxMIdAPSjlXNMaj6eHxxcLycHTJIje2YjSnwIQpF_zl_8fSL19FidimTvp846zhkT_Ka', title: '暗黑极简结构', cat: '设计' },
  { src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDBDdXJHpgfayeZzx-VsDDVny3wr9uMnrLiAdU-6hwfqs65GFTCUetnzJxP4qALuTtdgqS8-YKOWZ6EU0ko6brMkccBfi3WxZ54QSwpVvWnYopFdL55x_xthQnwk8FdgxKl1yse2ZoeYvM0V3l4qjY_cEaDpVYLIg6CyTsYd7cuhHiZWlOL6AbpJt3VKq57xhO-Nr8DVFvImNeVKHLeU-Y6XgY3Y9ceW8Hy1S--hWuah7HPkuMCnb4DQm37E-2IGnePVHyw8eJneSC_', title: '赛博霓虹光影', cat: '科技' },
];

const CATS = ['全部', '抽象艺术', '科技', '设计', '色彩'];

export default function Explore() {
  const [filter, setFilter] = useState('全部');
  const [selected, setSelected] = useState(null);
  const filtered = filter === '全部' ? GALLERY : GALLERY.filter(g => g.cat === filter);

  return (
    <Layout>
      <div className="p-4 md:p-8 max-w-[1600px] mx-auto">
        <div className="mb-8">
          <h2 className="font-hanken text-[24px] leading-8 font-semibold text-on-surface">设计探索</h2>
          <p className="text-on-surface-variant mt-1">Miketv AI 设计案例 · 激发无限创作灵感</p>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {CATS.map(c => (
            <button key={c} onClick={() => setFilter(c)} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter===c ? 'bg-primary text-on-primary' : 'border border-outline-variant text-on-surface-variant hover:border-primary'}`}>{c}</button>
          ))}
        </div>

        {/* Gallery grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((item, i) => (
            <div key={i} className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden group cursor-pointer hover:border-primary/50 hover:shadow-lg transition-all" onClick={() => setSelected(item)}>
              <div className="aspect-[1.6] overflow-hidden">
                <img src={item.src} alt={item.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy" />
              </div>
              <div className="p-3">
                <h4 className="font-semibold text-sm text-on-surface">{item.title}</h4>
                <span className="text-[10px] text-outline">{item.cat}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Lightbox */}
        {selected && (
          <div className="fixed inset-0 z-[200] bg-black/80 flex items-center justify-center p-4" onClick={() => setSelected(null)}>
            <div className="relative max-w-4xl max-h-[90vh]" onClick={e => e.stopPropagation()}>
              <button onClick={() => setSelected(null)} className="absolute -top-10 right-0 text-white hover:text-primary flex items-center gap-1"><Icon name="close" />关闭</button>
              <img src={selected.src} alt={selected.title} className="max-w-full max-h-[85vh] rounded-xl shadow-2xl" />
              <p className="text-white text-center mt-3">{selected.title} · {selected.cat}</p>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
