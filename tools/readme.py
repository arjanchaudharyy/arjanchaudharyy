#!/usr/bin/env python3
"""Writes README.md: the animated banner, then the plain profile text."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

README = '<picture><source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg"><img src="assets/hero-light.svg" width="100%" alt="hey, i\'m arjan. i build and break things."></picture>\n\nI\'m 16, from Nepal. A security researcher slowly getting into AI.\n\n**recent projects**\n\nbuilt the #1 Nepali TTS and STT models at [Naamche Labs](https://naamchelabs.com):\n\n- [Swar](https://github.com/Naamche-Labs/swar) (TTS): open Nepali text-to-speech that clones any voice from a short voice note ([launch video](https://x.com/ArjanChaudharyy/status/2115809203218755809))\n- [Kriti](https://github.com/Naamche-Labs/kriti) (STT): a compact, top-ranked Nepali speech recognition model ([launch](https://x.com/ArjanChaudharyy/status/2089748987264073815))\n- [Kriti Telephony](https://github.com/Naamche-Labs/kriti-telephony): Kriti tuned for real phone-call audio\n- [PagePatch](https://github.com/arjanchaudharyy/patch): a browser extension to permanently hide or rewrite anything on any website, editable with Claude Code\n- a bunch of security tooling and half-finished experiments across my repos\n\nmore at [arjanchaudharyy.com](https://www.arjanchaudharyy.com)\n'

with open(os.path.join(ROOT, "README.md"), "w") as f:
    f.write(README)
print("wrote README.md")
