import pathlib
src = pathlib.Path('sahou-harness/harness/desktop.py').read_text(encoding='utf-8')
print('has <script>:', src.count('<script>'))
print('has </script>:', src.count('</script>'))
i = src.find('<script')
print(repr(src[i-60:i+30]))
