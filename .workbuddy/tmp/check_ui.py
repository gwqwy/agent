import re, pathlib
src = pathlib.Path('sahou-harness/harness/desktop.py').read_text(encoding='utf-8')
start = src.index('UI_HTML')
end = src.index('</html>') + 7
html = src[src.index('<!DOCTYPE', start): end]
js = re.search(r'<script>(.*)</script>', html, re.S).group(1)
markup = html.replace(js, '')  # 去掉脚本，剩下的就是标记部分

ids = set(re.findall(r'id="([^"]+)"', markup))
refs = set(re.findall(r"\$\('([^']+)'\)", js))
print('missing ids:', sorted(r for r in refs if r not in ids) or 'NONE')

onclicks = set(re.findall(r'onclick="(\w+)\(', markup))
defs = set(re.findall(r'function\s+(\w+)\s*\(', js)) | set(re.findall(r'const\s+(\w+)\s*=', js))
print('missing onclick fns:', sorted(o for o in onclicks if o not in defs) or 'NONE')

for fn in ['notifyDone','updateRegenVisibility','regenerateLast','searchFlow','exportAll','loadUsageChart','applyAccent','applyFont','snipMenu','kbRemoveSource','toggleNotify','renderBrTabs','showBrFrame','brClose','brGo','playBeep']:
    if not re.search(r'function\s+'+fn+r'\s*\(', js):
        print('MISSING DEF:', fn)
print('done')
