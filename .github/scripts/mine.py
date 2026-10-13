# «Шахта дня»: раз в день спускается в шахту Minecraft на случайную глубину,
# добывает руду по правилам генерации мира и обновляет блок между
# <!--MINE:START--> и <!--MINE:END--> в README.md. Только стандартная библиотека.
import datetime
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
README = os.path.join(ROOT, "README.md")
LOG = os.path.join(ROOT, "mine", "log.json")

# руда: значок, мин. Y, макс. Y, пик Y, шанс в пике, сколько выпадает, ценность за штуку
OVERWORLD = {
    "Coal": ("⚫", 0, 128, 90, 100, (3, 12), 1),
    "Copper": ("🟠", -16, 112, 48, 60, (4, 15), 1),
    "Iron": ("⚪", -64, 72, 16, 70, (2, 8), 2),
    "Lapis": ("🔵", -64, 64, 0, 25, (4, 9), 2),
    "Redstone": ("🔴", -64, 15, -58, 35, (4, 10), 2),
    "Gold": ("🟡", -64, 32, -16, 18, (1, 6), 4),
    "Diamond": ("💎", -64, 16, -59, 8, (1, 4), 10),
    "Emerald": ("🟢", -16, 128, 100, 3, (1, 2), 12),
}
NETHER = {
    "Quartz": ("🤍", 10, 117, 60, 100, (4, 12), 1),
    "Nether Gold": ("🟡", 10, 117, 60, 60, (2, 8), 2),
    "Ancient Debris": ("🟤", 8, 22, 15, 6, (1, 2), 25),
}
NETHER_CHANCE = 0.12
ACCIDENTS = [  # (шанс, текст)
    (0.07, "💥 A creeper sneaked up from behind, trip ruined!"),
    (0.04, "🔥 Fell into lava, all the loot burned!"),
]
ORE_ICONS = {name: data[0] for name, data in {**OVERWORLD, **NETHER}.items()}


def weight(y, lo, hi, peak, top):
    if not lo <= y <= hi:
        return 0
    span = (peak - lo) if y <= peak else (hi - peak)
    return top * (1 - abs(y - peak) / span) if span else top


def dig(rng):
    for chance, text in ACCIDENTS:
        if rng.random() < chance:
            return {"accident": text}
    nether = rng.random() < NETHER_CHANCE
    ores = NETHER if nether else OVERWORLD
    y = rng.randint(8, 117) if nether else rng.randint(-64, 100)
    found = {}
    for _ in range(rng.randint(2, 4)):  # несколько жил за вылазку
        cands = [(n, weight(y, *d[1:5])) for n, d in ores.items()]
        cands = [(n, w) for n, w in cands if w > 0]
        if not cands:
            continue
        name = rng.choices([n for n, _ in cands], [w for _, w in cands])[0]
        lo, hi = ores[name][5]
        found[name] = found.get(name, 0) + rng.randint(lo, hi)
    value = sum(cnt * ores[n][6] for n, cnt in found.items())
    return {"dim": "nether" if nether else "overworld", "y": y, "ores": found, "value": value}


def fmt_date(iso):
    return datetime.date.fromisoformat(iso).strftime("%b %d, %Y")


def describe(t):
    if "accident" in t:
        return t["accident"]
    place = "🔥 Nether" if t["dim"] == "nether" else "⛰️ Overworld"
    ores = ", ".join(f"{ORE_ICONS[n]} {n} ×{c}" for n, c in sorted(t["ores"].items(), key=lambda kv: -kv[1]))
    return f"{place}, Y={t['y']}: {ores or 'nothing'} · value **{t['value']}**"


def main():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).date().isoformat()
    log = {"trips": 0, "accidents": 0, "inventory": {}, "record": None, "history": []}
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            log = json.load(f)

    if not log["history"] or log["history"][0]["date"] != today:
        trip = dig(random.Random(f"PaketikUWU-mine-{today}"))
        entry = {"date": today, "trip": trip}
        log["trips"] += 1
        if "accident" in trip:
            log["accidents"] += 1
        else:
            for n, c in trip["ores"].items():
                log["inventory"][n] = log["inventory"].get(n, 0) + c
            if not log["record"] or trip["value"] > log["record"]["trip"]["value"]:
                log["record"] = entry
        log["history"] = ([entry] + log["history"])[:7]
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    last = log["history"][0]
    inv = " · ".join(f"{ORE_ICONS[n]} {c}" for n, c in sorted(log["inventory"].items(), key=lambda kv: -kv[1]))
    lines = [f"> ⛏️ **Trip of {fmt_date(last['date'])}:** {describe(last['trip'])}"]
    if log["record"]:
        lines += [">", f"> 🏆 **Record:** {describe(log['record']['trip'])} ({fmt_date(log['record']['date'])})"]
    lines += [">", f"> 🎒 **Inventory:** {inv or 'empty'}",
              ">", f"> 🗺️ Trips: **{log['trips']}** · ☠️ Failures: **{log['accidents']}**",
              "", "<details><summary>Miner's log</summary>", "", "| Date | Trip |", "|---|---|"]
    lines += [f"| {fmt_date(e['date'])} | {describe(e['trip'])} |" for e in log["history"]]
    lines += ["", "</details>"]

    with open(README, encoding="utf-8") as f:
        text = f.read()
    start, end = "<!--MINE:START-->", "<!--MINE:END-->"
    a, b = text.index(start) + len(start), text.index(end)
    text = text[:a] + "\n" + "\n".join(lines) + "\n" + text[b:]
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


if __name__ == "__main__":
    main()
