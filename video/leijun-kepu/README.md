# 雷军 · 科普号单集（代码成片）

内容唯一来源：`雷军-科普号单集-最终执行包-2026-10-16.md`（Final v2）。

成片：`out/leijun_kepu_9x16.mp4`，1080×1920（9:16），30fps，106.5 秒，H.264 + AAC，响度约 -14 LUFS；封面帧 `out/cover.jpg`。

## 复现

```bash
sudo apt-get install -y ffmpeg fonts-noto-cjk   # 需要 Noto Sans CJK SC 字体
pip install -r requirements.txt
./build.sh            # TTS → 混音 → 渲染 → 合成，4 核约 1–2 分钟
./build.sh --preview 10,58.9,86.3   # 只导出静帧到 build/preview/
```

TTS 调用微软 Edge 在线语音服务，需要联网；生成结果缓存在 `build/tts/`，文案没变就不会重复请求。

## 技术栈

| 文件 | 作用 |
|------|------|
| `script.py` | 旁白切口、人物短句、开口时间、场景时间轴、年份卡 |
| `tts.py` | edge-tts：旁白用 `zh-CN-YunyangNeural`（纪录片稳），人物短句用另一路 `zh-CN-YunxiNeural`（非仿声）；同时记录逐词时间戳 |
| `audio.py` | numpy 合成配乐（Dm–B♭–F–C 铺底、低音脉冲、鼓点、年份卡重音、破发/点名重击、心跳、键盘声），人声闪避；输出 `build/mix.wav` 和驱动口型的 `build/char_env.npy` |
| `character.py` | PIL 绘制人物四个阶段（少年·武大 / 金山 / 小米创办 / 上市·造车），连续锚点为圆脸 + 圆框眼镜 + 短发，按阶段改变镜框粗细、发际线、发色和服装 |
| `render.py` | 逐帧绘制 S01–S08、年份时间轴、年份卡、字幕；多进程分段送入 ffmpeg/libx264，最后拼接，并用 loudnorm 合入音轨 |

依赖：Python 3.10+、Pillow、numpy、edge-tts、ffmpeg、Noto Sans CJK 字体、DejaVu Sans Mono 字体。

## 执行包要求的落实

- 旁白只进 S01、S03、S04–S05、S06–S07、S08；S02（机房/金山）和 2011 手机亮相留白，S02 只放画面字。
- 人物只说两句：「把 WPS 进行到底」（留在金山之后）、「愿意押上全部声誉」（造车段，并标注出处「2021.3.30 · 小米发布会」）。字幕用引号样式，不加「雷军：」。
- 三段反差：转互联网 vs 留下 → 四十岁"错过" vs 创办小米 → 破发收手 vs 加注造车。
- IPO：发行价 17.00、首日收盘 16.80（-1.2%）；日内曲线标注为"走势示意"，画面不显示其他价格。
- 年份卡：1969 / 1992 / 2010 / 2011 / 2018 / 2021。
- 结尾是提问卡和"评论区说"，没有"下一集"。
