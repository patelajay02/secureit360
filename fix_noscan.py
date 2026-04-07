content = open('app/dashboard/page.tsx', 'r', encoding='utf-8').read()
old = "{!dashboard?.ransom_score && ("
new = "{!dashboard?.ransom_score && !dashboard?.findings_summary && ("
if old in content:
    open('app/dashboard/page.tsx', 'w', encoding='utf-8').write(content.replace(old, new))
    print('SUCCESS')
else:
    print('NOT FOUND')
