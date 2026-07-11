# 의견 수집 연결 (구글 시트) 설정

정적 페이지에서 구글 시트에 직접 쓸 수 없으므로, **Google Apps Script 웹앱**을 경유한다.
계정: `jh.open.github@gmail.com`

## 1. 시트 생성
1. 위 계정으로 로그인 → [sheets.new](https://sheets.new) 로 새 시트 생성 (예: 이름 `hedge-board-feedback`).
2. 1행에 헤더 입력: `시각 | 이름 | 의견 | 페이지`

## 2. Apps Script 붙이기
1. 시트 상단 메뉴 **확장 프로그램 → Apps Script**.
2. 기본 코드를 지우고 아래 `Code.gs` 내용을 붙여넣기 → 저장.

```javascript
// Code.gs
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var sh = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    sh.appendRow([ new Date(), (data.name||'').toString().slice(0,80),
                   (data.text||'').toString().slice(0,2000), (data.page||'') ]);
    return ContentService.createTextOutput(JSON.stringify({ok:true}))
                         .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ok:false, error:String(err)}))
                         .setMimeType(ContentService.MimeType.JSON);
  }
}
```

## 3. 웹앱으로 배포
1. 우측 상단 **배포 → 새 배포**.
2. 유형(톱니바퀴) → **웹 앱**.
3. 설명 입력, **실행 계정: 나(me)**, **액세스 권한: 모든 사용자(Anyone)** 로 설정.
4. **배포** → 권한 승인(본인 계정).
5. 표시되는 **웹 앱 URL**을 복사 (형태: `https://script.google.com/macros/s/…/exec`).

## 4. 페이지에 연결
- `index.html`(과 `hedge-board.html`)의 `const FEEDBACK_ENDPOINT="";` 에 위 `/exec` URL을 넣는다.
- 커밋·푸시하면 활성화된다. (URL을 알려주면 대신 반영 가능.)

## 권한(누가 쓸 수 있나)에 대하여
- 웹앱을 "모든 사용자"로 열면 페이지 방문자 누구나 제출할 수 있다(공개 피드백의 특성).
- 남용이 우려되면: ① 스크립트에서 간단한 공유 토큰 확인, ② 제출 길이·빈도 제한, ③ 시트에서 수동 검토(권장) 로 관리한다.
- 페이지는 로컬 PC·DB에 접근하지 않으며, 의견은 오직 이 구글 시트에만 축적된다.
