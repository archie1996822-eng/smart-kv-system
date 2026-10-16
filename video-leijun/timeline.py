"""Card + shot timeline.

Every on-screen string below is copied verbatim from 「定稿剧本 v5」
(雷军-Cursor改片指令-v6-2026-10-16.md) – do not edit the text fields.

* CARDS  – text cards (captions / bubbles / gaps), one at a time, never overlapping.
* SHOTS  – visual shots. A card may span several shots (`scenes=[...]`) and a
           scene may span several cards (consecutive cards with trans="none").
* ITEMS  – alias of SHOTS (kept for audio.py), each shot also carries its card's
           text/kind/segment.

Segment boundaries follow the v5 time table and every boundary is snapped to a
96 BPM beat grid so the score lines up with the cuts.
"""
import re

FPS = 30
BPM = 96
BEAT = 60.0 / BPM          # 0.625 s
TOTAL = 180.0              # seconds

# (segment name, start s, end s, cards)
# card keys: text, kind(text|bubble|gap), scene | scenes=[(scene, fraction, trans_into)], style(sub|big),
#            hl=[highlighted words], grow=[enlarged words], trans (into the card), beats (fixed length),
#            min_beats
SEGMENTS = [
    ("1 钩子", 0, 12, [
        dict(text="四十岁，连雷军自己都说，错过了整个互联网。", scene="hook", hl=["错过"], grow=["错过"]),
        dict(text="可他人生最大的一把，偏偏从这时候才开始。", scene="hook", style="big", hl=["人生最大的一把"], trans="none"),
        dict(text="要看懂这一把，得从他年轻时说起。", scene="rewind_young", trans="flash"),
    ]),
    ("2 天赋与第一次失败", 12, 28, [
        dict(text="武汉大学，他两年修完了四年的学分。", scene="campus", hl=["两年", "四年"], trans="flash"),
        dict(text="大三，他和学长一起创业，失败了。", scene="closed_shop", hl=["失败了。"], trans="push"),
        dict(text="那是他第一次知道：光聪明，不够。", scene="alone_sit", style="big", hl=["光聪明，不够。"], trans="dip"),
    ]),
    ("3 盘古与辞职", 28, 58, [
        dict(text="一九九二年，他进了金山，做中国人自己的办公软件。", scene="kingsoft", hl=["一九九二年"], trans="wipe"),
        dict(text="一九九五年，他主导的「盘古」，卖不到预期的十分之一。", scene="pangu", hl=["十分之一"], trans="push"),
        dict(text="公司账上只剩十几万。", scene="ledger", style="big", hl=["十几万"], trans="dip"),
        dict(text="他看着对面楼里的灯，一盏一盏熄灭。", scene="lights", trans="dip"),
        dict(text="他递了辞职信，休了半年。", scene="resign", trans="dip"),
        dict(text="半年后，他还是回来了。这个决定，让他又多熬了十年。", scene="return_kingsoft", hl=["又多熬了十年"], trans="iris"),
    ]),
    ("4 守 WPS 的代价", 58, 88, [
        dict(text="回来以后，对手是微软，还有满街的盗版。", scene="squeeze", trans="wipe"),
        dict(text="他靠做别的软件赚钱，再把钱贴进 WPS。", scene="feed", trans="push"),
        dict(kind="bubble", text="把 WPS 进行到底", scene="bubble_wps", trans="flash", min_beats=6),
        dict(text="他守住了 WPS，却没赶上正在起来的互联网。", scene="window_wave", hl=["没赶上"], trans="fade"),
        dict(text="他说过：志存高远与顺势而为冲突时，我们选择了前者。", scene="mountain", hl=["志存高远"], trans="fade"),
        dict(text="意思是：他明知道那条路更顺，还是选了更难的那条。", scene="mountain", hl=["更难的那条"], trans="none"),
    ]),
    ("5 卓越网", 88, 104, [
        dict(text="二〇〇〇年，他还在金山，又创办了卓越网。", scene="joyo_story", hl=["二〇〇〇年"], trans="wipe"),
        dict(text="谈了至少三十家投资机构，一家都没成。", scene="joyo_story", hl=["三十家"], trans="none"),
        dict(text="最后只能卖掉。他说，就像失去了自己的孩子。", scene="joyo_story", trans="none"),
    ]),
    ("6 想明白与离开", 104, 130, [
        dict(text="那几年他反复想一件事：为什么这么拼，还是没赶上？", scene="night_ponder", trans="dip"),
        dict(text="二〇〇六年，他想明白了：他说过，成功靠勤奋远远不够。",
             scenes=[("think", 0.42, "fade"), ("river", 0.58, "fade")], hl=["二〇〇六年"], trans="fade"),
        dict(text="顺势而为。", scene="shunshi", style="big", hl=["顺势而为。"], trans="flash", min_beats=7),
        dict(text="二〇〇七年，金山终于上市。同一年，他卸任离开。", scene="leave", hl=["二〇〇七年"], trans="wipe"),
        dict(text="在金山，他守了十六年。", scene="rings", hl=["十六年"], trans="fade"),
    ]),
    ("7 再押一次", 130, 170, [
        dict(text="二〇一〇年，四十岁，他决定从零开始做手机。",
             scenes=[("forty", 0.45, "dip"), ("blueprint", 0.55, "iris")], hl=["四十岁", "从零开始"], trans="dip"),
        dict(text="这一次，他先看准了方向，再全力去做。", scene="summit", hl=["先看准了方向"], trans="fade"),
        dict(text="八年后，小米走到了上市这一天。", scene="ipo_gong", hl=["八年后"], trans="wipe"),
        dict(text="可第一天，就跌破发行价。", scene="crash", hl=["跌破发行价"], trans="flash"),
        dict(text="所有人都以为，这次他该收手了。", scene="doubt", trans="dip"),
        dict(kind="gap", text="", scene="black", trans="cut", beats=1),
        dict(text="近三年后，他宣布造车。", scene="car", hl=["造车"], trans="cut"),
        dict(kind="bubble", text="愿意押上全部声誉", scene="bubble_allin", trans="flash", min_beats=6),
        dict(text="二〇二四年，第一辆车发布。", scene="launch", hl=["二〇二四年"], trans="flash"),
    ]),
    ("收尾", 170, 180, [
        dict(text="前面输掉的那些年，没有白费。", scene="path", trans="fade"),
        dict(text="晚，从来不是不开始的理由。", scene="sunrise", style="big", trans="fade"),
    ]),
]

PUNCT = re.compile(r"[，。：「」、？ ]")


def _raw(card):
    if card["kind"] == "bubble":
        return 3.9
    n = len(PUNCT.sub("", card["text"]))
    d = n / 4.4 + 1.25
    if card["style"] == "big":
        d += 0.6
    return d


def _distribute(total_beats, cards):
    fixed = sum(c.get("beats", 0) for c in cards)
    flex = [c for c in cards if "beats" not in c]
    avail = total_beats - fixed
    raw = [_raw(c) for c in flex]
    k = avail / sum(raw)
    want = [max(r * k, c.get("min_beats", 3)) for r, c in zip(raw, flex)]
    k2 = avail / sum(want)
    want = [w * k2 for w in want]
    base = [int(w) for w in want]
    rem = avail - sum(base)
    order = sorted(range(len(want)), key=lambda i: want[i] - base[i], reverse=True)
    for i in order[:rem]:
        base[i] += 1
    for c, b in zip(flex, base):
        c["beats"] = b
        if b < c.get("min_beats", 0):
            raise ValueError(f"segment too short for {c['text']}")


def build():
    cards = []
    for si, (seg, s0, s1, items) in enumerate(SEGMENTS):
        b0, b1 = round(s0 / BEAT), round(s1 / BEAT)
        seg_cards = []
        for it in items:
            c = dict(it)
            c.setdefault("kind", "text")
            c.setdefault("style", "sub")
            c.setdefault("hl", [])
            c.setdefault("grow", [])
            c.setdefault("trans", "fade")
            c["segment"] = seg
            c["seg_index"] = si
            seg_cards.append(c)
        _distribute(b1 - b0, seg_cards)
        b = b0
        for c in seg_cards:
            c["start"] = b * BEAT
            b += c["beats"]
            c["end"] = b * BEAT
        cards.extend(seg_cards)
    cards[-1]["end"] = TOTAL

    shots = []
    for ci, c in enumerate(cards):
        parts = c.get("scenes") or [(c["scene"], 1.0, c["trans"])]
        bstart = round(c["start"] / BEAT)
        nb = c["beats"]
        acc = 0.0
        for pi, (scene, frac, tr) in enumerate(parts):
            sb = bstart + round(acc * nb)
            acc += frac
            eb = bstart + round(acc * nb) if pi < len(parts) - 1 else None
            st = sb * BEAT
            en = eb * BEAT if eb is not None else c["end"]
            trans = c["trans"] if pi == 0 else tr
            if shots and trans == "none" and shots[-1]["scene"] == scene:
                shots[-1]["end"] = en
                shots[-1]["cards"].append(ci)
                continue
            shots.append(dict(scene=scene, start=st, end=en, trans=trans, cards=[ci],
                              text=c["text"], kind=c["kind"], segment=c["segment"], seg_index=c["seg_index"]))
    for s in shots:
        s["scene_start"] = s["start"]
        s["scene_end"] = s["end"]
        s["scene_items"] = [(max(cards[ci]["start"], s["start"]) - s["start"],
                             min(cards[ci]["end"], s["end"]) - s["start"]) for ci in s["cards"]]
        s["scene_k"] = 0
    for c in cards:
        c["shot"] = next(s for s in shots if s["start"] <= c["start"] < s["end"] or
                         (s["start"] <= c["start"] and s["end"] >= c["end"]))["scene"]
    return cards, shots


CARDS, SHOTS = build()
ITEMS = SHOTS


def _at(lst, t):
    for i, it in enumerate(lst):
        if t < it["end"] or i == len(lst) - 1:
            return i, it
    return len(lst) - 1, lst[-1]


def shot_at(t):
    return _at(SHOTS, t)


def card_at(t):
    return _at(CARDS, t)


item_at = shot_at


if __name__ == "__main__":
    print("CARDS")
    for c in CARDS:
        print(f'{c["start"]:7.2f} {c["end"]:7.2f} {c["end"]-c["start"]:5.2f}  {c["kind"]:6s} {c["text"]}')
    print("SHOTS")
    for s in SHOTS:
        print(f'{s["start"]:7.2f} {s["end"]:7.2f} {s["end"]-s["start"]:5.2f}  {s["scene"]:14s} {s["trans"]:6s} cards={s["cards"]}')
    print("total", CARDS[-1]["end"])
