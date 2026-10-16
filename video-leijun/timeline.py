"""Shot list. Every on-screen string below is copied verbatim from
《雷军-创意脚本-定稿-2026-10-16.md》 – do not edit the text fields.

Timing is derived from the text length (~4.4 chars/s reading pace plus breathing
room), then scaled to the target runtime and snapped to a 96 BPM beat grid so
the generated score lines up with the cuts.
"""
import re

FPS = 30
BPM = 96
BEAT = 60.0 / BPM          # 0.625 s
TOTAL = 150.0              # seconds

# kind: text | bubble ; style: sub (lower third) | big (centred title card)
# trans: transition INTO this item (none = same continuous scene)
SEGMENTS = [
    ("1 钩子", [
        dict(text="四十岁，连雷军自己都说，错过了整个互联网。", scene="hook", hl=["错过了整个互联网"]),
        dict(text="但他最狠的一把，才刚开始。", scene="hook", style="big", hl=["最狠的一把"], trans="none"),
    ]),
    ("过渡", [
        dict(text="回到二十多年前。", scene="rewind", style="big", trans="flash"),
    ]),
    ("2 起点", [
        dict(text="武汉大学，他两年修完了四年的学分。", scene="campus", hl=["两年", "四年"], trans="flash"),
        dict(text="大三，他和学长一起创业。", scene="startup", trans="push"),
        dict(text="失败了。最惨的时候，连饭票都要靠赢来换。", scene="startup", hl=["失败了。"], trans="none"),
    ]),
    ("3 代价", [
        dict(text="一九九二年，他进了金山。", scene="kingsoft", hl=["一九九二年"], trans="wipe"),
        dict(text="一九九五年，他主导的「盘古」，卖不到预期的十分之一。", scene="pangu", hl=["十分之一"], trans="push"),
        dict(text="账上只剩十几万。", scene="ledger", style="big", hl=["十几万"], trans="dip"),
        dict(text="他看着对面楼里的灯，一盏一盏熄灭。", scene="lights", trans="dip"),
    ]),
    ("4 低谷", [
        dict(text="他递了辞职信，休了半年。", scene="resign", trans="dip"),
        dict(text="半年后，他又回来了。", scene="return", trans="iris"),
    ]),
    ("5 坚持", [
        dict(text="微软和盗版两头夹击。", scene="squeeze", hl=["两头夹击"], trans="wipe"),
        dict(text="他靠做别的软件，养活 WPS。", scene="feed", trans="push"),
        dict(kind="bubble", text="把 WPS 进行到底", scene="bubble_wps", trans="flash"),
        dict(text="他说过：志存高远与顺势而为冲突时，我们选择了前者。", scene="mountain", hl=["志存高远"], trans="fade"),
    ]),
    ("6 再输一次", [
        dict(text="他还创办了卓越网。", scene="joyo", trans="wipe"),
        dict(text="谈了至少三十家投资机构，一家都没成。", scene="doors", hl=["三十家"], trans="push"),
        dict(text="最后只能卖掉。他说，就像失去了自己的孩子。", scene="balloon", trans="fade"),
    ]),
    ("7 转折", [
        dict(text="二〇〇六年，离开金山前一年，他想明白了一件事。", scene="think", hl=["二〇〇六年"], trans="dip"),
        dict(text="他说过，成功靠勤奋远远不够。", scene="river", trans="fade"),
        dict(text="顺势而为。", scene="river", style="big", hl=["顺势而为。"], trans="none"),
    ]),
    ("8 离开", [
        dict(text="二〇〇七年，金山终于上市，他却在同一年卸任。", scene="leave", hl=["二〇〇七年"], trans="wipe"),
        dict(text="在金山，这一守就是十六年。", scene="rings", hl=["十六年"], trans="fade"),
    ]),
    ("9 重来", [
        dict(text="二〇一〇年，四十岁。", scene="forty", style="big", hl=["四十岁。"], trans="dip"),
        dict(text="他说过：人生目标还没有完成，愿意再去试一把。", scene="summit", hl=["再去试一把"], trans="fade"),
        dict(text="他从零开始做手机。", scene="blueprint", hl=["从零开始"], trans="iris"),
    ]),
    ("10 破发", [
        dict(text="二〇一八年，公司上市，第一天就跌破发行价。", scene="crash", hl=["跌破发行价"], trans="flash"),
        dict(text="所有人都以为，这次他该收手了。", scene="doubt", trans="dip"),
    ]),
    ("11 高潮", [
        dict(text="近三年后，他做了一个更大的决定：造车。", scene="car", hl=["造车。"], trans="dip"),
        dict(kind="bubble", text="愿意押上全部声誉", scene="bubble_allin", trans="flash"),
        dict(text="二〇二四年，第一辆车发布。", scene="launch", hl=["二〇二四年"], trans="flash"),
    ]),
    ("12 收尾", [
        dict(text="摔过的每一跤，都没有白摔。", scene="path", trans="fade"),
        dict(text="晚，从来不是不开始的理由。", scene="sunrise", style="big", trans="fade"),
    ]),
]

PUNCT = re.compile(r"[，。：「」、 ]")


def _raw_duration(item, first_in_segment, last):
    if item.get("kind") == "bubble":
        d = 3.6
    else:
        n = len(PUNCT.sub("", item["text"]))
        d = n / 4.4 + 1.25
        if item.get("style") == "big":
            d += 0.5
    if first_in_segment:
        d += 0.6
    if last:
        d += 2.4      # ending hold / fade out
    return d


def build():
    flat = []
    for si, (seg, items) in enumerate(SEGMENTS):
        for ii, it in enumerate(items):
            it = dict(it)
            it.setdefault("kind", "text")
            it.setdefault("style", "sub")
            it.setdefault("hl", [])
            it.setdefault("trans", "fade")
            it["segment"] = seg
            it["seg_index"] = si
            last = si == len(SEGMENTS) - 1 and ii == len(items) - 1
            it["raw"] = _raw_duration(it, ii == 0, last)
            flat.append(it)
    total_raw = sum(i["raw"] for i in flat)
    k = TOTAL / total_raw
    beats_total = round(TOTAL / BEAT)
    acc = 0.0
    prev_b = 0
    for it in flat:
        acc += it["raw"] * k
        b = min(beats_total, round(acc / BEAT))
        b = max(b, prev_b + 3)
        it["start"] = prev_b * BEAT
        it["end"] = b * BEAT
        it["beats"] = (prev_b, b)
        prev_b = b
    flat[-1]["end"] = TOTAL
    # group consecutive items that share a scene into one continuous scene
    sc_start = 0
    for i, it in enumerate(flat):
        if i > 0 and flat[i - 1]["scene"] == it["scene"] and it["trans"] == "none":
            it["scene_start"] = flat[sc_start]["start"]
            it["scene_k"] = flat[i - 1]["scene_k"] + 1
        else:
            sc_start = i
            it["scene_start"] = it["start"]
            it["scene_k"] = 0
    for it in flat:
        group = [x for x in flat if x["scene_start"] == it["scene_start"]]
        it["scene_end"] = group[-1]["end"]
        it["scene_items"] = [(x["start"] - it["scene_start"], x["end"] - it["scene_start"]) for x in group]
    return flat


ITEMS = build()


def item_at(t):
    for i, it in enumerate(ITEMS):
        if t < it["end"] or i == len(ITEMS) - 1:
            return i, it
    return len(ITEMS) - 1, ITEMS[-1]


if __name__ == "__main__":
    for it in ITEMS:
        print(f'{it["start"]:7.2f} {it["end"]:7.2f} {it["end"]-it["start"]:5.2f}  {it["scene"]:12s} {it["trans"]:6s} {it["text"]}')
    print("total", ITEMS[-1]["end"])
