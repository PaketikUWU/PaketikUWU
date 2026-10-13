# «Факт дня»: раз в день показывает новый факт о Python или Java (языки чередуются)
# в блоке между <!--FACT:START--> и <!--FACT:END--> в README.md.
# Факты не повторяются, пока не будут показаны все. Только стандартная библиотека.
import datetime
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
README = os.path.join(ROOT, "README.md")
FACTS = os.path.join(ROOT, "facts", "facts.json")
LOG = os.path.join(ROOT, "facts", "log.json")

LANGS = {
    "python": ("🐍", "Python", "python"),
    "java": ("☕", "Java", "java"),
}


def main():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).date()
    with open(FACTS, encoding="utf-8") as f:
        facts = json.load(f)
    log = {"date": None, "lang": None, "index": None, "shown": {lang: [] for lang in LANGS}}
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            log = json.load(f)

    if log["date"] != today.isoformat():
        lang = "java" if log["lang"] == "python" else "python"
        shown = log["shown"].setdefault(lang, [])
        left = [i for i in range(len(facts[lang])) if i not in shown]
        if not left:  # все факты показаны — начинаем круг заново
            shown.clear()
            left = list(range(len(facts[lang])))
        index = random.Random(f"PaketikUWU-fact-{today}").choice(left)
        shown.append(index)
        log.update(date=today.isoformat(), lang=lang, index=index)
        with open(LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    lang, fact = log["lang"], facts[log["lang"]][log["index"]]
    icon, name, hl = LANGS[lang]
    total = sum(len(v) for v in facts.values())
    seen = sum(len(v) for v in log["shown"].values())
    block = "\n".join([
        f"**{icon} {name} · {fact['title']}**",
        "",
        fact["text"],
        "",
        f"```{hl}",
        fact["code"],
        "```",
        "",
        f"<sub>{today.strftime('%b %d, %Y')} · {seen} of {total} shown · tomorrow: "
        f"{'Java' if lang == 'python' else 'Python'}</sub>",
    ])

    with open(README, encoding="utf-8") as f:
        text = f.read()
    start, end = "<!--FACT:START-->", "<!--FACT:END-->"
    a, b = text.index(start) + len(start), text.index(end)
    text = text[:a] + "\n" + block + "\n" + text[b:]
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


if __name__ == "__main__":
    main()
