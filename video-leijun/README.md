# 雷军 · 科普号单集（折纸风动画演绎）

依据《雷军-创意脚本-定稿-2026-10-16.md》用纯代码渲染的动画短片工程，可随时重渲。

- 规格：1920×1080，16:9，30fps，H.264（High / yuv420p）+ AAC，时长 150.0 秒，无配音
- 风格：折纸 / 纸艺。画面带折痕分面、纸纤维纹理、层叠纸片投影；字幕印在折纸丝带上，大标题用层叠剪纸字
- 人物：风格化的折纸角色（短发侧分、圆脸、笑容），不是写实真人
- 气泡台词只有「把 WPS 进行到底」「愿意押上全部声誉」两句
- 每一帧右上角都有「AI生成·动画演绎」角标
- 不用小米 LOGO、发布会画面或原声；画面里的软件盒、手机、汽车都是通用造型，没有品牌标识
- 音乐和音效全部由 `audio.py` 用程序合成（不含任何采样或现成曲目），属于原创，可商用
- 字体：Noto Serif CJK SC / Noto Sans CJK SC（SIL OFL 许可，可商用）

## 目录

| 文件 | 作用 |
|---|---|
| `timeline.py` | 分镜表：上屏文字（与定稿逐字一致）、场景、转场；按字数自动算时长（约 3～4.5 字/秒），对齐 96 BPM 节拍网格 |
| `scenes_a.py` / `scenes_b.py` | 各镜头画面（第 1～6 段 / 第 7～12 段） |
| `character.py` | 折纸角色骨架：姿势、表情、不同年龄段服装、走路、背影 |
| `gfx.py` | 绘图工具：缓动、折纸分面、纸纹理、纸片投影等 |
| `audio.py` | 程序合成配乐 + 音效，输出 `build/audio.wav` |
| `render.py` | 合成帧、转场、字幕、角标，多进程编码，最后与音频封装成 mp4 |

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
python3 render.py --sheet         # 每个镜头的缩略图拼板 -> build/sheet_*.png
python3 render.py --cover         # 封面「错过时代的人」-> output/封面-错过时代的人.png
python3 audio.py                  # 只重做音频
```

4 核机器上整片渲染约 7～8 分钟。

## 修改

- **文字或节奏**：编辑 `timeline.py` 的 `SEGMENTS`。`hl` 是需要高亮的词，`style="big"` 是居中大标题，`trans` 是进入该镜头的转场（fade / flash / wipe / push / iris / dip / none）。
- **大标题位置**：改 `render.py` 里的 `BIG_POS`。
- **画面**：每个镜头对应一个 `@scene("名字")` 函数。参数 `S.t` 是镜头内的时间，`S.T` 是镜头总时长。
