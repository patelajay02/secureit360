content = open('app/dashboard/page.tsx', 'r', encoding='utf-8').read()
old = '        <p className="text-center text-gray-700 text-xs mt-8">'
new = '''        {dashboard?.ransom_score && (
          <div className="bg-gray-900 border border-red-800 rounded-2xl p-6 mt-6 text-center">
            <p className="text-red-400 font-semibold text-lg mb-2">You are on a free trial</p>
            <p className="text-gray-400 text-sm mb-4">Your free trial includes Dark Web and Email Security scans only. Upgrade to unlock all 6 scan engines, full Ransom Risk Score, Governance Score, and regulatory compliance mapping.</p>
            <a href="/pricing" className="inline-block bg-red-600 hover:bg-red-700 text-white font-semibold px-8 py-3 rounded-lg">Subscribe Now - from $250 NZD/month + GST</a>
          </div>
        )}
        <p className="text-center text-gray-700 text-xs mt-8">'''
if old in content:
    open('app/dashboard/page.tsx', 'w', encoding='utf-8').write(content.replace(old, new))
    print('SUCCESS')
else:
    print('NOT FOUND')
