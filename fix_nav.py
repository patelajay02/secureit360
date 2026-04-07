content = open('app/dashboard/page.tsx', 'r', encoding='utf-8').read()
old = '          <div className="flex items-center gap-6">\n            <span className="text-gray-400 text-sm">{companyName}</span>\n            <button onClick={handleLogout} className="text-gray-400 hover:text-white \ntext-sm">\n              Sign out\n            </button>\n          </div>'
new = '          <div className="flex items-center gap-6">\n            <a href="/dashboard" className="text-gray-400 hover:text-white text-sm">Dashboard</a>\n            <a href="/dashboard/scanning" className="text-gray-400 hover:text-white text-sm">Run Scan</a>\n            <a href="/settings" className="text-gray-400 hover:text-white text-sm">Settings</a>\n            <span className="text-gray-400 text-sm">{companyName}</span>\n            <button onClick={handleLogout} className="text-gray-400 hover:text-white text-sm">Sign out</button>\n          </div>'
if old in content:
    open('app/dashboard/page.tsx', 'w', encoding='utf-8').write(content.replace(old, new))
    print('SUCCESS')
else:
    print('NOT FOUND')
