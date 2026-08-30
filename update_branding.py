import re
from pathlib import Path

files_to_update = [
    Path('static/js/slashCommands.js'),
    Path('static/js/sessions.js'),
    Path('static/js/keyboard-shortcuts.js'),
    Path('static/js/tasks.js'),
    Path('static/js/presets.js'),
    Path('static/js/settings.js'),
    Path('static/js/theme.js'),
    Path('static/js/emailLibrary.js'),
    Path('static/index.html'),
    Path('static/login.html'),
    Path('src/visual_report.py'),
    Path('src/reminder_personas.py'),
]

replacements = [
    ("'Odysseus'", "'MultiVision'"),
    ('"Odysseus"', '"MultiVision"'),
    ('Odysseus Chat', 'MultiVision Chat'),
    ('Welcome to Odysseus', 'Welcome to MultiVision'),
    ('Odysseus is yours', 'MultiVision is yours'),
    ('ask Odysseus in chat', 'ask MultiVision in chat'),
    ('Odysseus will create', 'MultiVision will create'),
    ('Odysseus reaches for', 'MultiVision reaches for'),
    ('Odysseus nudges you', 'MultiVision nudges you'),
    ('Odysseus tools', 'MultiVision tools'),
    ('Odysseus Logo', 'MultiVision Logo'),
    ('Odysseus default theme', 'MultiVision default theme'),
    ('Odysseus Deep Research', 'MultiVision Deep Research'),
    ('Odysseus &mdash; Deep Research', 'MultiVision &mdash; Deep Research'),
    ('You are Odysseus', 'You are MultiVision'),
]

for p in files_to_update:
    if not p.exists():
        continue
    content = p.read_text(encoding='utf-8')
    orig = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != orig:
        p.write_text(content, encoding='utf-8')
        print(f"Updated: {p}")

print("Branding update finished successfully!")
