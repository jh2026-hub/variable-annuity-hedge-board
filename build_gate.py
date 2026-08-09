#!/usr/bin/env python3
"""열람코드 게이트 빌더 — 평문 페이지를 AES-GCM 암호문 한 덩어리로 감싼다.

  python build_gate.py .private/track.src.html track.html "헷지손익 관리"

정적 호스팅에서 자바스크립트 비교문으로 막는 건 보호가 아니다(소스에 본문이 그대로 남는다).
여기서는 **본문 자체를 암호화**해 코드를 모르면 복호가 불가능하게 한다.
PBKDF2-HMAC-SHA256 150,000회 → AES-256-GCM. 원본 cases.html(2026-07-17) 과 같은 규약.

평문은 .private/ 에 두고 git 에 올리지 않는다. 코드는 인자/환경변수로만 받는다(레포에 없음).
해제 후에는 document.write 로 문서를 통째로 교체한다 — 스크립트가 있는 앱 페이지도
그대로 동작하게 하려면 innerHTML 주입으로는 안 된다(주입된 <script> 는 실행되지 않는다).
"""
import base64, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITER = 150_000

def build(src: str, dst: str, title: str, code: str) -> None:
    pt = open(src, encoding="utf-8").read().encode()
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                     iterations=ITER).derive(code.encode())
    ct = AESGCM(key).encrypt(iv, pt, None)
    b = lambda x: base64.b64encode(x).decode()
    blob = json.dumps({"s": b(salt), "i": b(iv), "d": b(ct)}, separators=(",", ":"))
    open(dst, "w", encoding="utf-8").write(PAGE.replace("__TITLE__", title)
                                               .replace("__BLOB__", blob)
                                               .replace("__KEYNS__", os.path.basename(dst)))
    print(f"{dst}: 평문 {len(pt):,}B → 암호문 {len(ct):,}B")

PAGE = """<!doctype html><html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>__TITLE__</title>
<style>
  :root{color-scheme:light}
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:#F4F6FA;color:#16202F;
    font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Pretendard",sans-serif}
  .g{width:min(340px,88vw);background:#fff;border-radius:16px;padding:30px 24px;text-align:center;
    box-shadow:0 2px 20px rgba(22,32,47,.09)}
  .lk{font-size:30px}
  h1{font-size:15px;margin:12px 0 3px}
  p{font-size:11.5px;color:#8A94A6;margin:0 0 18px}
  input{width:100%;box-sizing:border-box;padding:11px;font-size:17px;text-align:center;
    letter-spacing:5px;border:1px solid #DDE3EE;border-radius:10px;background:#F8FAFD}
  input:focus{outline:none;border-color:#4A6FC4}
  button{width:100%;margin-top:9px;min-height:44px;border:0;border-radius:10px;
    background:#4A6FC4;color:#fff;font-size:13.5px;font-weight:800;cursor:pointer}
  #e{font-size:11.5px;color:#B8455F;min-height:17px;margin-top:9px}
  a{display:inline-block;margin-top:6px;font-size:11px;color:#8A94A6}
</style></head><body>
<div class="g">
  <div class="lk">🔒</div>
  <h1>__TITLE__</h1>
  <p>열람 코드를 입력하세요</p>
  <input id="p" type="password" inputmode="numeric" maxlength="12" autocomplete="off" autofocus>
  <button id="b">열기</button>
  <div id="e"></div>
  <a href="./index.html">← 교육판으로</a>
</div>
<script>
const B=__BLOB__, K="ck:__KEYNS__";
const u8=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
async function open_(pw,quiet){
  const e=document.getElementById('e');
  if(!pw){ if(!quiet) e.textContent='코드를 입력하세요'; return; }
  try{
    const km=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
    const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:u8(B.s),iterations:150000,hash:'SHA-256'},
      km,{name:'AES-GCM',length:256},false,['decrypt']);
    const pt=await crypto.subtle.decrypt({name:'AES-GCM',iv:u8(B.i)},key,u8(B.d));
    try{sessionStorage.setItem(K,pw);}catch(_){}
    /* 스크립트가 든 문서라 innerHTML 주입으론 안 돈다 — 문서를 통째로 교체 */
    document.open(); document.write(new TextDecoder().decode(pt)); document.close();
  }catch(_){
    try{sessionStorage.removeItem(K);}catch(__){}
    if(!quiet){ e.textContent='코드가 맞지 않아요'; document.getElementById('p').value=''; }
  }
}
document.getElementById('b').onclick=()=>open_(document.getElementById('p').value.trim());
document.getElementById('p').onkeydown=ev=>{if(ev.key==='Enter')open_(ev.target.value.trim());};
try{const c=sessionStorage.getItem(K); if(c) open_(c,true);}catch(_){}
</script></body></html>"""

if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    code = os.environ.get("GATE_CODE") or (sys.argv[4] if len(sys.argv) > 4 else "")
    if not code:
        sys.exit("열람코드가 없습니다 — GATE_CODE 환경변수 또는 4번째 인자")
    build(sys.argv[1], sys.argv[2], sys.argv[3], code)
