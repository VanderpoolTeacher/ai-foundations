#!/usr/bin/env python3
"""
Build a publishable copy of a deck: strips every speaker note, removes the
notes panel and its keybinding, and adds a noindex tag.

    python3 build-public-deck.py "<working deck>.html" decks/session-N-name.html

The working copies keep their notes. Nothing with a data-notes attribute
should ever land in this repository.
"""
import io
import re
import sys


def strip_notes(s):
    """Remove every data-notes attribute.

    Scans to the quote that actually closes the attribute rather than the
    first one found -- the notes contain angle brackets and entities, so a
    naive regex truncates the <section> tag and silently breaks the slide.
    """
    removed = 0
    while True:
        i = s.find(' data-notes="')
        if i == -1:
            return s, removed
        j = i + len(' data-notes="')
        while True:
            q = s.find('"', j)
            if q == -1:
                raise ValueError("unterminated data-notes attribute")
            k = q + 1
            while k < len(s) and s[k] in " \t\r\n":
                k += 1
            if k < len(s) and s[k] == ">":
                break
            j = q + 1
        s = s[:i] + s[q + 1:]
        removed += 1


def main(src, dst):
    s = io.open(src, encoding="utf-8").read()
    slides_before = s.count('<section class="slide')

    s, removed = strip_notes(s)

    # the notes panel, written with either a literal or an escaped separator
    s = re.sub(r'<div id="notes">.*?</div>\s*</div>\s*\n?', "", s, count=1, flags=re.S)

    # its keybinding and the line that fills it
    s = re.sub(r"\s*else if\(e\.key==='n'\|\|e\.key==='N'\)np\.classList\.toggle\('on'\);", "", s)
    s = re.sub(r"\s*nb\.innerHTML=s\[i\]\.dataset\.notes\|\|'<i>No notes\.</i>';", "", s)
    s = s.replace(
        "      bar=document.getElementById('bar'),nb=document.getElementById('nb'),np=document.getElementById('notes');",
        "      bar=document.getElementById('bar');",
    )
    s = s.replace(
        "document.addEventListener('click',function(e){ if(!e.target.closest('#notes')) show(i+1) });",
        "document.addEventListener('click',function(){ show(i+1) });",
    )

    tag = '<meta name="viewport" content="width=device-width, initial-scale=1">'
    if "noindex" not in s and s.count(tag) == 1:
        s = s.replace(tag, tag + '\n<meta name="robots" content="noindex, nofollow">', 1)

    problems = []
    if s.count("data-notes"):
        problems.append("data-notes attributes survived")
    if 'id="notes"' in s or 'id="nb"' in s:
        problems.append("notes panel survived")
    if "nb." in s or "np." in s:
        problems.append("orphaned notes-panel JS reference")
    if s.count('<section') != s.count('</section>'):
        problems.append("unbalanced <section> tags")
    if s.count('<section class="slide') != slides_before:
        problems.append("slide count changed")
    for tagstr in re.findall(r'<section\b.*?>', s, re.S):
        if "<div" in tagstr or "<p " in tagstr:
            problems.append("a <section> tag swallowed a child element")
            break
    if problems:
        sys.exit("REFUSING TO WRITE:\n  " + "\n  ".join(problems))

    io.open(dst, "w", encoding="utf-8").write(s)
    print(f"{dst}: {slides_before} slides, {removed} notes removed, clean")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
