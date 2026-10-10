# Novaris data format v1

Source of truth: `Novaris_Grundstruktur_v1_4_Standalone_Korrigiert.html`.

The source is an offline HTML document with embedded base64 image resources. Run `python3 tools/extract.py /path/to/Novaris_Grundstruktur_v1_4_Standalone_Korrigiert.html` to extract losslessly preserved HTML fragments, scene metadata, and binary images into separate files. Requires `beautifulsoup4`.

## File structure

- `data/people/*.json`: person records including original HTML fragments
- `data/districts/*.json`: district records including original HTML fragments
- `data/world/*.json`: world records including original HTML fragments
- `data/scenes/*.json`: scenes with all original fields
- `media/*`: decoded image bytes
- `manifest.json`: version, path, size and SHA-256 of every file

The extractor generates stable IDs from semantic identifiers and a deterministic collision suffix. `source_html` retains the original semantic HTML subtree, with image data URIs replaced by relative media paths. JSON string values are not rewritten. The extractor does not delete files already present in the output directory.

## Update protocol

Clients fetch the manifest over HTTPS, compare per-file SHA-256 hashes, download changed files only, verify length and SHA-256, validate the complete candidate dataset, then atomically switch the active generation. On any failure, keep the previous generation. Retain previously installed media until the new generation has been committed. Data versions are independent of APK versions.

**Important:** The current Android app's original monolithic updater is not compatible with this sharded manifest until its new downloader has been deployed. Do not publish a manifest as ready until a complete extraction and app-side integration test succeeds.
