// Besucherzähler: erhöht pro Aufruf nur eine Zahl pro Tag. Es werden keine Daten über Besucher gespeichert.
// Einrichten: siehe README, Abschnitt «Besucherzähler».
function doGet() {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Besuche') ||
             SpreadsheetApp.getActiveSpreadsheet().insertSheet('Besuche');
    if (sh.getLastRow() === 0) sh.appendRow(['Datum', 'Aufrufe']);
    var heute = Utilities.formatDate(new Date(), 'Europe/Zurich', 'yyyy-MM-dd');
    var n = sh.getLastRow();
    var letzte = n > 1 ? sh.getRange(n, 1).getValue() : '';
    if (letzte instanceof Date) letzte = Utilities.formatDate(letzte, 'Europe/Zurich', 'yyyy-MM-dd');
    if (letzte === heute) {
      var z = sh.getRange(n, 2);
      z.setValue(Number(z.getValue()) + 1);
    } else {
      sh.appendRow([heute, 1]);
      sh.getRange(sh.getLastRow(), 1).setNumberFormat('@').setValue(heute);
    }
  } finally {
    lock.releaseLock();
  }
  return ContentService.createTextOutput('ok');
}
