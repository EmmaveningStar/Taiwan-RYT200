// 在「表單回覆試算表」的 擴充功能 → Apps Script 貼上。
// 執行 setupApprovalSheet 一次，再部署為網頁應用程式。
// 僅輸出「審核狀態」為「已核准」的列，不輸出時間戳記或其他欄位。
function setupApprovalSheet() {
  const book = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = book.getSheets().find(s =>
    s.getRange(1, 1, 1, Math.max(s.getLastColumn(), 1))
      .getDisplayValues()[0].some(h => h.trim() === '投稿內容'));
  if (!sheet) throw new Error('找不到含「投稿內容」欄的回覆工作表');
  const properties = PropertiesService.getScriptProperties();
  properties.setProperty('SPREADSHEET_ID', book.getId());
  properties.setProperty('SHEET_ID', String(sheet.getSheetId()));
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn())
    .getDisplayValues()[0].map(h => h.trim());
  let col = headers.indexOf('審核狀態') + 1;
  if (!col) {
    col = sheet.getLastColumn() + 1;
    sheet.getRange(1, col).setValue('審核狀態');
  }
  const rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['待審核', '已核准', '不公開'], true)
    .setAllowInvalid(false).build();
  if (sheet.getMaxRows() > 1) {
    sheet.getRange(2, col, sheet.getMaxRows() - 1, 1)
      .setDataValidation(rule);
  }
}

function doGet() {
  const props = PropertiesService.getScriptProperties();
  const book = SpreadsheetApp.openById(props.getProperty('SPREADSHEET_ID'));
  const sheetId = Number(props.getProperty('SHEET_ID'));
  const sheet = book.getSheets().find(s => s.getSheetId() === sheetId);
  if (!sheet) throw new Error('請先執行 setupApprovalSheet');
  const rows = sheet.getDataRange().getDisplayValues();
  const headers = rows.shift().map(h => h.trim());
  function index(label) {
    const pos = headers.indexOf(label);
    if (pos < 0) throw new Error('缺少欄位：' + label);
    return pos;
  }
  const approval = index('審核狀態');
  const body = index('投稿內容');
  const host = index('主辦教室/老師');
  const city = index('縣市');
  const source = index('相關連結');
  const notes = rows.filter(r =>
    r[approval].trim() === '已核准' && r[body].trim()
  ).map(r => ({
    approved: true,
    title: [r[host].trim(), r[city].trim()].filter(Boolean).join('｜') || '讀者投稿',
    body: r[body].trim(),
    url: /^https:\/\//i.test(r[source].trim()) ? r[source].trim() : ''
  }));
  return ContentService.createTextOutput(JSON.stringify({version: 1, notes}))
    .setMimeType(ContentService.MimeType.JSON);
}
