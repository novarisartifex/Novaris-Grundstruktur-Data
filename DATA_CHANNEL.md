# Novaris Grundstruktur — Datenkanal

Die Originalquelle ist `Novaris_Grundstruktur_v1_3_Standalone.html` (113.504.062 Bytes, Google Drive).

## Sicherheitsmodell
- Daten-Releases werden erst nach Extraktion, Inhaltsprüfung und vollständigem Upload veröffentlicht.
- `manifest.json` enthält zunächst **keine** veröffentlichte Version.
- Später: HTTPS-Download, SHA-256, Größenlimit, Versionsprüfung, Staging-Datei, Validierung, atomarer Wechsel, Backup und Rollback.
- HTML/JavaScript gilt als ausführbarer Anwendungscode, **nicht** als beliebig austauschbare Datenbank. Für Online-Updates werden zuerst reine Daten/Medien vom Programmcode getrennt.
- Niemals ein ungeprüftes HTML-Paket über den Datenkanal ausführen.

Die Quelldatei enthält eingebettete Bilder und JavaScript. Es wurde noch kein Daten-Release erzeugt.
