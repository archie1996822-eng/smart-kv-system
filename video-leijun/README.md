# 雷军 · 科普号单集（折纸风动画演绎）

依据《雷军-创意脚本-定稿-2026-10-16.md》用纯代码渲染的动画短片工程，可随时重渲。当前版本按
`docs/雷军-Cursor改片指令-v6-2026-10-16.md`（上屏文字为文末「定稿剧本 v5」）修改。

- 规格：1920×1080，16:9，30fps，H.264（High / yuv420p）+ AAC 48 kHz，时长 180.0 秒，无配音
- 响度：整体 -14 LUFS（EBU R128），真峰值低于 -1 dBTP
- 风格：折纸 / 纸艺。画面带折痕分面、纸纤维纹理、层叠纸片投影；字幕印在折纸丝带上，大标题用层叠剪纸字
- 人物：风格化的折纸角色（短发侧分、圆脸、黑框圆眼镜），不是写实真人
- 气泡台词只有「把 WPS 进行到底」「愿意押上全部声誉」两句，各停留 3 秒以上
- 字卡一张一张出：上一张完全消失后才出下一张，整行同时显现，不会残留单字；底部字幕条离画面底边 76px
- 每一帧右上角都有「AI生成·动画演绎」角标
- 不用小米 LOGO、发布会画面或原声；画面里的软件盒、手机、汽车、锣都是通用造型，没有品牌标识
- 音乐和音效全部由 `audio.py` 用程序合成（不含任何采样或现成曲目），属于原创，可商用
- 字体：Noto Serif CJK SC / Noto Sans CJK SC（SIL OFL 许可，可商用）

## 目录

| 文件 | 作用 |
|---|---|
| `timeline.py` | 字卡表 `CARDS`（与 v5 逐字一致）和镜头表 `SHOTS`；按字数自动算时长，对齐 96 BPM 节拍网格 |
| `scenes_a.py` / `scenes_b.py` | 原有镜头画面 |
| `scenes_c.py` | v6 新增镜头：时间回卷变年轻、关门的小摊、独坐、推门回金山+翻日历、窗外浪潮、卓越网、深夜想问题、顺势而为、走出大楼、上市敲锣、黑场 |
| `character.py` | 折纸角色骨架：姿势、表情、不同年龄段服装、走路、背影 |
| `gfx.py` | 绘图工具：缓动、折纸分面、纸纹理、纸片投影等 |
| `audio.py` | 程序合成配乐 + 音效，输出 `build/audio.wav` |
| `render.py` | 合成帧、转场、字幕、角标，多进程编码，最后与音频封装成 mp4 |
| `check.py` | 自检：字卡与 v5 逐字比对、同一时间只有一张字卡、换卡前无残字（像素比对）、气泡和「顺势而为」时长、黑场、底边距离、成片规格与响度 |

## 环境

```bash
sudo apt-get install -y ffmpeg fonts-noto-cjk libcairo2-dev pkg-config
pip install -r requirements.txt
```

## 渲染

```bash
python3 render.py                 # 成片 -> output/雷军-科普号单集-动画演绎.mp4
python3 render.py --jobs 4        # 指定并行进程数
python3 render.py --still 33.5    # 导出单帧预览 -> build/still_33.50.png
python3 render.py --sheet         # 每张字卡两帧的缩略图拼板 -> build/sheet_*.png
python3 render.py --cover         # 封面「错过时代的人」-> output/封面-错过时代的人.png
python3 check.py --video          # 渲完后自检（含成片规格与响度）
```

4 核机器上整片渲染约 12 分钟。

## 修改

- **文字或节奏**：编辑 `timeline.py` 的 `SEGMENTS`。`hl` 是高亮词，`grow` 是放大词，`style="big"` 是居中大标题，`trans` 是进入该镜头的转场（fade / flash / wipe / push / iris / dip / cut / none），`scenes=[...]` 让一张字卡跨多个镜头，`min_beats` 设最短停留拍数。
- **大标题位置 / 字号**：改 `render.py` 里的 `BIG_POS` / `BIG_SIZE`。
- **画面**：每个镜头对应一个 `@scene("名字")` 函数。参数 `S.t` 是镜头内的时间，`S.T` 是镜头总时长，`S.items` 是镜头内各字卡的起止时间。
