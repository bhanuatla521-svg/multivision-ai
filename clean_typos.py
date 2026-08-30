from pathlib import Path

typos = {
    'vedio': 'video',
    'vedioes': 'videos',
    'feactureses': 'features',
    'feacture': 'feature',
    'internate': 'internet',
    'commends': 'commands',
    'chart bar': 'chat bar',
    'hole project': 'whole project',
    'funtionall': 'functional',
}

files = [
    Path('static/index.html'),
    Path('static/media.html'),
    Path('static/login.html'),
    Path('src/youtube_handler.py'),
    Path('src/nvidia_helper.py'),
]

fixed_count = 0
for f in files:
    if not f.exists(): 
        continue
    text = f.read_text(encoding='utf-8')
    orig = text
    for bad, good in typos.items():
        if bad in text:
            text = text.replace(bad, good)
            print(f'Fixed typo "{bad}" -> "{good}" in {f}')
    if text != orig:
        f.write_text(text, encoding='utf-8')
        fixed_count += 1

print(f"Finished typo scan. Files cleaned: {fixed_count}")
