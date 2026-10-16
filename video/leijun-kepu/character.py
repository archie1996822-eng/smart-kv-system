"""代码绘制的人物半身像（四个年龄阶段，执行包 D 节）。

连续锚点：圆脸 + 圆框眼镜 + 短发；随阶段变化的是脸型饱满度、镜框粗细、发际线、发色、服装。
所有精灵图以 3 倍超采样绘制后缩小，得到抗锯齿边缘；结果按 (stage, mouth, eyes) 缓存。
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

SS = 3
SPRITE_W, SPRITE_H = 600, 800

SKIN = (240, 203, 168)
SKIN_SHADE = (222, 178, 142)
SKIN_LINE = (150, 98, 72)
BLUSH = (236, 150, 130)

STAGES = {
    # 1 少年·武大：瘦，细圆框，整齐短发，白衬衫
    1: dict(rx=200, ry=244, cheek=0.02, hair=(28, 26, 30), hair_top=0.20, hairline=-0.50,
            recede=0.00, part=0.0, gray=0.0, frame=6, frame_col=(70, 52, 40),
            shoulder=1.95, outfit="shirt", smile=0.7),
    # 2 金山：短发偏分，细框，衬衫 + 薄外套
    2: dict(rx=206, ry=246, cheek=0.04, hair=(30, 28, 32), hair_top=0.17, hairline=-0.47,
            recede=0.03, part=1.0, gray=0.0, frame=7, frame_col=(55, 45, 40),
            shoulder=2.05, outfit="jacket", smile=0.8),
    # 3 小米创办：圆脸、发际略后移、标志性黑框圆眼镜、深色圆领
    3: dict(rx=232, ry=246, cheek=0.10, hair=(30, 30, 34), hair_top=0.11, hairline=-0.56,
            recede=0.07, part=0.6, gray=0.12, frame=15, frame_col=(18, 18, 22),
            shoulder=2.15, outfit="crew", smile=1.0),
    # 4 上市·造车：发白增多、头顶更疏、黑框、黑西装
    4: dict(rx=238, ry=248, cheek=0.12, hair=(92, 92, 98), hair_top=0.07, hairline=-0.60,
            recede=0.11, part=0.5, gray=0.55, frame=15, frame_col=(16, 16, 20),
            shoulder=2.2, outfit="suit", smile=0.85),
}


def _s(v):
    return int(round(v * SS))


def _face_poly(cx, cy, rx, ry, cheek, n=180):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        s, c = math.sin(t), math.cos(t)
        k = 1.0
        if s > 0:  # 下半脸：圆润的腮部
            k += cheek * 4 * s * (1 - s)
        x = cx + rx * c * k
        y = cy + ry * s * (1.0 if s < 0 else 0.97)
        pts.append((x, y))
    return pts


def _mask(size):
    return Image.new("L", size, 0)


def _paste_color(img, color, mask):
    layer = Image.new("RGBA", img.size, color + (255,))
    img.paste(layer, (0, 0), mask)


def _draw_body(img, p, cx, top):
    d = ImageDraw.Draw(img)
    W, H = img.size
    sw = p["rx"] * p["shoulder"] * SS
    neck_w = p["rx"] * 0.62 * SS
    # 脖子
    d.rounded_rectangle([cx - neck_w / 2, top - _s(70), cx + neck_w / 2, top + _s(70)],
                        radius=_s(30), fill=SKIN_SHADE)
    body_top = top + _s(40)
    outfit = p["outfit"]
    base = {"shirt": (236, 238, 242), "jacket": (198, 186, 160), "crew": (28, 40, 66),
            "suit": (22, 24, 30)}[outfit]
    body = [(cx - sw / 2, H), (cx - sw / 2, body_top + _s(130)),
            (cx - sw / 2 + _s(40), body_top + _s(40)), (cx - _s(60), body_top),
            (cx + _s(60), body_top), (cx + sw / 2 - _s(40), body_top + _s(40)),
            (cx + sw / 2, body_top + _s(130)), (cx + sw / 2, H)]
    d.polygon(body, fill=base)
    d.ellipse([cx - sw / 2, body_top, cx - sw / 2 + _s(160), body_top + _s(220)], fill=base)
    d.ellipse([cx + sw / 2 - _s(160), body_top, cx + sw / 2, body_top + _s(220)], fill=base)

    if outfit == "shirt":
        d.polygon([(cx - neck_w / 2 - _s(10), body_top - _s(20)), (cx, body_top + _s(90)),
                   (cx - _s(95), body_top + _s(70))], fill=(250, 250, 252), outline=(190, 194, 205),
                  width=_s(3))
        d.polygon([(cx + neck_w / 2 + _s(10), body_top - _s(20)), (cx, body_top + _s(90)),
                   (cx + _s(95), body_top + _s(70))], fill=(250, 250, 252), outline=(190, 194, 205),
                  width=_s(3))
        d.line([(cx, body_top + _s(90)), (cx, H)], fill=(205, 208, 216), width=_s(3))
        for k in range(3):
            y = body_top + _s(150 + k * 90)
            d.ellipse([cx - _s(7), y - _s(7), cx + _s(7), y + _s(7)], fill=(200, 203, 212))
    elif outfit == "jacket":
        shirt = (176, 204, 232)
        d.polygon([(cx - _s(110), body_top), (cx + _s(110), body_top), (cx + _s(60), H),
                   (cx - _s(60), H)], fill=shirt)
        d.polygon([(cx - neck_w / 2 - _s(8), body_top - _s(18)), (cx, body_top + _s(80)),
                   (cx - _s(80), body_top + _s(60))], fill=(196, 220, 242))
        d.polygon([(cx + neck_w / 2 + _s(8), body_top - _s(18)), (cx, body_top + _s(80)),
                   (cx + _s(80), body_top + _s(60))], fill=(196, 220, 242))
        lap = (172, 160, 134)
        d.polygon([(cx - _s(120), body_top + _s(10)), (cx - _s(40), H), (cx - _s(150), H),
                   (cx - _s(190), body_top + _s(200))], fill=lap)
        d.polygon([(cx + _s(120), body_top + _s(10)), (cx + _s(40), H), (cx + _s(150), H),
                   (cx + _s(190), body_top + _s(200))], fill=lap)
    elif outfit == "crew":
        d.chord([cx - neck_w / 2 - _s(26), body_top - _s(70), cx + neck_w / 2 + _s(26),
                 body_top + _s(56)], 0, 180, fill=(20, 30, 52))
        d.chord([cx - neck_w / 2 - _s(8), body_top - _s(60), cx + neck_w / 2 + _s(8),
                 body_top + _s(36)], 0, 180, fill=SKIN_SHADE)
    elif outfit == "suit":
        tee = (30, 34, 46)
        d.polygon([(cx - _s(120), body_top), (cx + _s(120), body_top), (cx + _s(70), H),
                   (cx - _s(70), H)], fill=tee)
        d.chord([cx - neck_w / 2 - _s(22), body_top - _s(70), cx + neck_w / 2 + _s(22),
                 body_top + _s(50)], 0, 180, fill=(40, 44, 58))
        d.chord([cx - neck_w / 2 - _s(6), body_top - _s(60), cx + neck_w / 2 + _s(6),
                 body_top + _s(32)], 0, 180, fill=SKIN_SHADE)
        lap = (12, 13, 17)
        d.polygon([(cx - _s(130), body_top + _s(10)), (cx - _s(60), H), (cx - _s(170), H),
                   (cx - _s(210), body_top + _s(220))], fill=lap)
        d.polygon([(cx + _s(130), body_top + _s(10)), (cx + _s(60), H), (cx + _s(170), H),
                   (cx + _s(210), body_top + _s(220))], fill=lap)


def _hairline(x, cx, cy, p):
    rx, ry = p["rx"] * SS, p["ry"] * SS
    u = (x - cx) / rx
    y = cy + ry * p["hairline"]
    # 额头弧形：中间高、两侧低
    y += ry * 0.12 * min(1.0, u * u / 0.6)
    # 侧分刘海：从分线向另一侧斜扫
    if p["part"] > 0:
        y += ry * 0.06 * p["part"] * max(0.0, min(1.0, (u + 0.35) / 0.9)) * (1 - abs(u) ** 3)
    # 鬓角
    y += ry * 0.55 * max(0.0, abs(u) - 0.8) / 0.2
    # 发际线后移（M 形）
    y -= ry * p["recede"] * math.exp(-((abs(u) - 0.55) ** 2) / 0.025)
    return y


def _draw_hair(img, p, cx, cy):
    W, H = img.size
    rx, ry = p["rx"] * SS, p["ry"] * SS
    m = _mask((W, H))
    dm = ImageDraw.Draw(m)
    top = cy - ry * (1 + p["hair_top"])
    dm.ellipse([cx - rx * 1.06, top, cx + rx * 1.06, cy + ry * 0.75], fill=255)
    cut = _mask((W, H))
    dc = ImageDraw.Draw(cut)
    xs = np.linspace(cx - rx * 1.1, cx + rx * 1.1, 160)
    pts = [(x, _hairline(x, cx, cy, p)) for x in xs]
    dc.polygon([(cx - rx * 1.2, 0)] + pts + [(cx + rx * 1.2, 0)], fill=255)
    m = ImageChops.multiply(m, cut)
    _paste_color(img, p["hair"], m)
    tex = _mask((W, H))
    dt = ImageDraw.Draw(tex)
    for k in range(-6, 7):
        x0 = cx + k * rx * 0.15
        dt.arc([x0 - rx * 0.55, top + ry * 0.04, x0 + rx * 0.45, top + ry * 1.0], 205, 245,
               fill=150, width=_s(3))
    hl = tuple(min(255, c + 45) for c in p["hair"])
    _paste_color(img, hl, ImageChops.multiply(tex, m))
    if p["gray"] > 0:
        g = _mask((W, H))
        dg = ImageDraw.Draw(g)
        for sx in (-1, 1):
            dg.ellipse([cx + sx * rx * 0.98 - rx * 0.16, cy - ry * 0.55, cx + sx * rx * 0.98 + rx * 0.16,
                        cy + ry * 0.25], fill=int(255 * p["gray"]))
        dg.ellipse([cx - rx * 0.7, top, cx + rx * 0.7, top + ry * 0.35], fill=int(170 * p["gray"]))
        g = ImageChops.multiply(g, m).filter(ImageFilter.GaussianBlur(_s(10)))
        _paste_color(img, (214, 214, 218), g)


def _draw_face(img, p, cx, cy, mouth, eyes):
    W, H = img.size
    rx, ry = p["rx"] * SS, p["ry"] * SS
    d = ImageDraw.Draw(img)
    # 耳朵
    for sx in (-1, 1):
        ex = cx + sx * rx * 0.97
        d.ellipse([ex - rx * 0.13, cy - ry * 0.16, ex + rx * 0.13, cy + ry * 0.24], fill=SKIN_SHADE)
        d.ellipse([ex - rx * 0.07, cy - ry * 0.09, ex + rx * 0.07, cy + ry * 0.17], fill=(214, 166, 132))
    poly = _face_poly(cx, cy, rx, ry, p["cheek"])
    d.polygon(poly, fill=SKIN)
    # 侧面阴影
    sh = _mask((W, H))
    ImageDraw.Draw(sh).polygon(poly, fill=255)
    off = _mask((W, H))
    ImageDraw.Draw(off).polygon([(x - rx * 0.12, y) for x, y in poly], fill=255)
    shade = ImageChops.subtract(sh, off).filter(ImageFilter.GaussianBlur(_s(12)))
    shade = shade.point(lambda v: int(v * 0.55))
    _paste_color(img, SKIN_SHADE, shade)
    # 腮红
    bl = _mask((W, H))
    db = ImageDraw.Draw(bl)
    for sx in (-1, 1):
        bx = cx + sx * rx * 0.55
        db.ellipse([bx - rx * 0.17, cy + ry * 0.22, bx + rx * 0.17, cy + ry * 0.38], fill=70)
    _paste_color(img, BLUSH, bl.filter(ImageFilter.GaussianBlur(_s(14))))

    ey = cy - ry * 0.02
    exs = [cx - rx * 0.37, cx + rx * 0.37]
    smile = p["smile"]
    brow_col = tuple(int(c * 0.9) for c in p["hair"]) if p["gray"] < 0.3 else (70, 66, 66)
    for ex in exs:
        d.arc([ex - rx * 0.22, ey - ry * 0.44, ex + rx * 0.22, ey - ry * 0.12], 205, 335,
              fill=brow_col, width=_s(11))
    eye_col = (36, 28, 26)
    for ex in exs:
        if eyes == "blink":
            d.arc([ex - rx * 0.1, ey - ry * 0.06, ex + rx * 0.1, ey + ry * 0.06], 10, 170,
                  fill=eye_col, width=_s(6))
        elif eyes == "smile":
            d.arc([ex - rx * 0.1, ey - ry * 0.03, ex + rx * 0.1, ey + ry * 0.1], 195, 345,
                  fill=eye_col, width=_s(7))
        else:
            d.ellipse([ex - rx * 0.062, ey - ry * 0.055, ex + rx * 0.062, ey + ry * 0.065], fill=eye_col)
            d.ellipse([ex - rx * 0.03, ey - ry * 0.035, ex + rx * 0.0, ey - ry * 0.005],
                      fill=(255, 255, 255))
    # 鼻子
    d.arc([cx - rx * 0.1, cy + ry * 0.12, cx + rx * 0.1, cy + ry * 0.28], 20, 160,
          fill=SKIN_LINE, width=_s(5))
    d.ellipse([cx - rx * 0.075, cy + ry * 0.21, cx - rx * 0.035, cy + ry * 0.245], fill=(196, 140, 110))
    d.ellipse([cx + rx * 0.035, cy + ry * 0.21, cx + rx * 0.075, cy + ry * 0.245], fill=(196, 140, 110))
    # 嘴
    my = cy + ry * 0.47
    mw = rx * (0.30 + 0.06 * smile)
    if mouth == 0:
        d.arc([cx - mw, my - ry * 0.16, cx + mw, my + ry * 0.07 * (0.6 + smile)], 18, 162,
              fill=(150, 70, 60), width=_s(7))
    else:
        oh = ry * (0.08 if mouth == 1 else 0.15)
        box = [cx - mw * 0.82, my - oh * 0.5, cx + mw * 0.82, my + oh * 1.1]
        d.chord(box, 0, 180, fill=(112, 40, 40))
        d.rectangle([box[0], my - oh * 0.5, box[2], my - oh * 0.5 + oh * 0.5], fill=(112, 40, 40))
        d.rounded_rectangle([cx - mw * 0.6, my - oh * 0.48, cx + mw * 0.6, my - oh * 0.48 + oh * 0.45],
                            radius=_s(6), fill=(250, 248, 244))
        if mouth == 2:
            d.ellipse([cx - mw * 0.38, my + oh * 0.35, cx + mw * 0.38, my + oh * 1.0], fill=(206, 98, 96))
    # 眼镜
    fr = rx * 0.255
    fw = _s(p["frame"])
    col = p["frame_col"]
    lens = _mask((W, H))
    dl = ImageDraw.Draw(lens)
    for ex in exs:
        dl.ellipse([ex - fr, ey - fr * 0.95, ex + fr, ey + fr * 0.95], fill=36)
    _paste_color(img, (210, 230, 255), lens)
    for ex in exs:
        d.ellipse([ex - fr, ey - fr * 0.95, ex + fr, ey + fr * 0.95], outline=col, width=fw)
        d.arc([ex - fr * 0.7, ey - fr * 0.7, ex + fr * 0.7, ey + fr * 0.7], 200, 240,
              fill=(255, 255, 255), width=_s(4))
    d.arc([cx - rx * 0.13, ey - fr * 0.55, cx + rx * 0.13, ey + fr * 0.15], 200, 340, fill=col,
          width=max(_s(5), fw * 2 // 3))
    for sx in (-1, 1):
        x0 = cx + sx * (rx * 0.37 + fr)
        d.line([(x0, ey - fr * 0.25), (cx + sx * rx * 0.93, ey - fr * 0.4)], fill=col,
               width=max(_s(5), fw * 2 // 3))


@lru_cache(maxsize=64)
def sprite(stage, mouth=0, eyes="open"):
    """返回 RGBA 精灵图，尺寸 SPRITE_W × SPRITE_H，头部中心约在 (300, 340)。"""
    p = STAGES[stage]
    W, H = SPRITE_W * SS, SPRITE_H * SS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx, cy = W // 2, _s(340)
    neck_top = cy + p["ry"] * SS * 0.9
    _draw_body(img, p, cx, neck_top)
    _draw_face(img, p, cx, cy, mouth, eyes)
    _draw_hair(img, p, cx, cy)
    # 轻描边
    a = img.split()[3]
    edge = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(7)), a)
    outline = Image.new("RGBA", (W, H), (10, 16, 32, 255))
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    base.paste(outline, (0, 0), edge.point(lambda v: int(v * 0.5)))
    base.alpha_composite(img)
    out = base.resize((SPRITE_W, SPRITE_H), Image.LANCZOS)
    # 身体下缘渐隐，避免半身像出现硬切边
    fade = np.ones(SPRITE_H)
    f0 = int(SPRITE_H * 0.78)
    fade[f0:] = np.linspace(1, 0, SPRITE_H - f0) ** 1.5
    a = np.asarray(out.getchannel("A"), dtype=np.float32) * fade[:, None]
    out.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    return out


if __name__ == "__main__":
    from pathlib import Path
    out = Path(__file__).parent / "build"
    out.mkdir(exist_ok=True)
    sheet = Image.new("RGBA", (SPRITE_W * 4, SPRITE_H * 2), (14, 30, 58, 255))
    for i, st in enumerate((1, 2, 3, 4)):
        sheet.alpha_composite(sprite(st, 0, "open"), (i * SPRITE_W, 0))
        sheet.alpha_composite(sprite(st, 2, "smile"), (i * SPRITE_W, SPRITE_H))
    sheet.convert("RGB").save(out / "character_sheet.png")
    print("saved", out / "character_sheet.png")
