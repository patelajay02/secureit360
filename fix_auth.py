content = open('lib/auth.js', 'r', encoding='utf-8').read()
old = """export function isTokenExpired(token) {
  const decoded = decodeToken(token);
  if (!decoded || !decoded.exp) return true;
  return Date.now() / 1000 > decoded.exp;
}"""
new = """export function isTokenExpired(token) {
  try {
    const decoded = decodeToken(token);
    if (!decoded || !decoded.exp) return false;
    return Date.now() / 1000 > decoded.exp;
  } catch {
    return false;
  }
}"""
if old in content:
    open('lib/auth.js', 'w', encoding='utf-8').write(content.replace(old, new))
    print('SUCCESS')
else:
    print('NOT FOUND')
