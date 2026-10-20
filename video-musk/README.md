# 马斯克 · 科普号（纯代码逐帧绘制）

依据《马斯克·科普号创意脚本 v0.4.1》制作（脚本原文：`script_v0.4.1.md`）。全部画面由 Python + cairo 逐帧绘制、ffmpeg 合成，没有用任何视频生成模型。

> 当前状态：**已选定方向 B（新闻剪报拼贴）**，人物改为卡通动画造型，待确认人物后做开场分镜与前三十秒。

## 方向 B 卡通人物优化稿（待确认）

| 文件 | 内容 |
|---|---|
| `release/v3/board_B_toon.jpg` | 人物对比（2008 西装白衬衫 / 2026 黑 T 恤）+ 表情稿 |
| `release/v3/B_collage_portrait.png` | 原尺寸人物对比帧，字卡「二零零八年。」「十八年后。」 |
| `release/v3/B_collage_expressions.png` | 表情稿：2008 笑 / 低谷 / 不收手，2026 平静（设计稿，标注不上屏） |

人物代码：`style3/toon.py`。剪纸分层（身体、脖子、头、耳朵、头发各一层，层间小投影）+ 墨线五官 + 网点阴影与网点腮红 + 白边贴纸。
特征取自参考照：宽方下巴、高发际线带前额上翘的发束、粗平浓眉、窄笑眼、咧嘴露上齿；2026 版鬓角发灰、额纹、眼袋、法令纹、双下巴、下颌更宽。

## 第三轮：三个风格方向（待选）

| 文件 | 内容 |
|---|---|
| `release/v3/board_A.jpg` | 方向 A · 电影感暗调插画：夜景硬光、明暗色块塑形、冷色轮廓光、胶片颗粒 |
| `release/v3/board_B.jpg` | 方向 B · 新闻剪报拼贴：剪纸、网点印刷、胶带字卡、纸张纹理 |
| `release/v3/board_C.jpg` | 方向 C · 扁平矢量动画：干净色块、柔和渐变、圆润造型 |
| `release/v3/*_apex.png`、`*_portrait.png` | 各方向的 1920×1080 原尺寸单帧 |

- 轨道按参考图：地面引道 → 右侧弯起 → 垂直 → 顶端向回卷的半环；右侧桁架塔 + 顶部悬臂。车在顶端倒挂在轨道下方，四道白 / 淡蓝冷气朝下喷，无橙色火焰。
- 人物：三个方向共用 `style3/geo.py` 里的同一套脸部结构（按参考照比例勾出：宽脸、高发际线、短发上竖、浓眉压眼、窄眼、笑时露上齿），只换配色与质感处理；2026 版加额纹、眼袋、加深法令纹、双下巴、鬓角发灰、下脸更宽。
- 样张上屏文字均取自脚本原句：「短暂悬停。翻转。再落下。」「二零零八年。」「十八年后。」

```bash
cd style3 && python3 frames.py        # 生成 A/B/C 全部样张；也可 python3 frames.py A
```

## 第二版：折纸风格静态稿（待确认）

第一版的 3D 低多边形方案已经否掉。第二版改成 2D 手工设计的折纸 / 纸雕风格，先只出图片：

| 文件 | 内容 |
|---|---|
| `release/paper_style_frame.png` | 开场风格样张：U 形半圆跑道，车在顶部被四道冷气托住悬停 |
| `release/paper_opening_storyboard.png` | 开场动作分解：冲刺、爬壁、冲顶、悬停、翻转点喷校准姿态、减速落地 |
| `release/paper_character_sheet.png` | 人物形象稿：2008 / 2026 |

绘制代码：`origami.py`（折纸工具：折痕分面、投影、裁切边）、`paper_open.py`（开场场景、纸模型汽车、冷气）、
`portrait.py`（纸雕肖像）、`portrait_sheet.py`、`paper_still.py`。

```bash
python3 paper_still.py style release/paper_style_frame.png
python3 paper_still.py board release/paper_opening_storyboard.png
python3 portrait_sheet.py release/paper_character_sheet.png
```

## 规格

- 1920×1080，16:9，30 fps，H.264 High / yuv420p + AAC 48 kHz，无配音
- 响度用 loudnorm 归一（样片实测 -15.6 LUFS，真峰值 -1.8 dBFS）
- 音乐与音效全部由 `audio.py` 用程序合成（不含采样、不含现成曲目），原创，可商用

## 风格做法

- `mesh.py`：通用低多边形渲染器。每个面单色平面着色，相邻面在折痕处硬切；面与面之间描一道细亮边，像纸的折线
- 场景是真 3D 分层（远山三层 / 机库与塔台 / 地面折面 / 坡道与车 / 前景石块和锥桶），机位移动时各层自然产生视差；远山背后有纸板厚度面
- 天空是分层剪纸色带，不用平滑渐变；全画面叠一层纸纤维纹理
- 人物：`head.py` 用横截面放样出长脸，再加高眉骨、深眼窝 + 眼球、直鼻梁、颧骨、方下巴等体积；眼睛、眉、唇、皱纹是贴在曲面上的折片，不是贴图。`character.py` 把脖子从下颌内侧放样进衣领，头身一体；衣服翻领、衬衫 V 领是单独剪出的纸片层，带可见厚度
- 年龄：`age=0`（2008）发际线更低、头发更厚、几乎无纹；`age=1`（2026）鬓角发灰、额纹、眼袋、法令纹、木偶纹、眼皮更沉、下脸略重

## 开场（`scene_open.py`）

| 时间 | 动作 |
|---|---|
| 0.00–1.00 s | 第一帧车已在坡上高速爬升（带速度线），沿四分之一圆弧坡加速到 80° |
| 1.00–1.58 s | 冲出坡顶，车头朝天，减速到顶点 |
| 1.50 s | 四个喷口同时开启 |
| 1.58–2.50 s | 顶点停一瞬，车底四道淡蓝白冷气托住车身悬停，轻微浮动 |
| 2.50–3.32 s | 后空翻 360°，冷气减弱、雾气散开 |
| 3.32–3.88 s | 喷口关闭，加速下落 |
| 3.88 s | 落地：悬挂压缩回弹、灰白扬尘、镜头震动，此处接字卡钩子 |

喷流颜色只有 `#f4f9ff / #d6ebff / #a9d2f5`（白、淡蓝），场景里也没有任何暖色光源。`check.py` 会逐帧统计橙黄色像素占比。

## 命令

```bash
sudo apt-get install -y ffmpeg python3-cairo python3-numpy python3-scipy fonts-noto-cjk
python3 render.py open            # -> output/开场特技样片.mp4
python3 render.py turn            # -> output/形象转面.mp4
python3 render.py open --still 2.1
python3 sheets.py                 # -> output/形象稿-马斯克.png、形象稿-表情.png、动作分解稿-开场.png
python3 check.py output/开场特技样片.mp4
python3 stills.py build/o 0 1.6 2.2 && python3 montage.py build/m.png build/o_*.png   # 关键帧拼板
```

## 文件

| 文件 | 作用 |
|---|---|
| `gfx.py` | 缓动、颜色、纸片厚度 `slab`、纸纹理 |
| `mesh.py` | 低多边形网格、透视相机、画家算法排序 + 平面着色 |
| `head.py` | 马斯克头部网格（年龄参数）+ 五官折片 + 表情参数 |
| `character.py` | 折纸身体、脖子、手臂、服装（2008 西装 / 2026 T 恤外套） |
| `car.py` | 通用低多边形跑车（无品牌标识）+ 四个冷气喷口 |
| `scene_open.py` | 开场特技：运动曲线、机位、冷气粒子、扬尘、分层场景 |
| `scene_char.py` | 人物转面、棚拍背景 |
| `audio.py` | 程序合成配乐与音效 |
| `render.py` | 多进程逐帧渲染 → ffmpeg 编码 → 混音封装 |
| `sheets.py` | 形象稿、表情稿、动作分解稿 |
| `check.py` | 自检：规格、火焰色像素、首帧是否在动、响度 |
