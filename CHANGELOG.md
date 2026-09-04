# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-09-04

### Added
- `--auto-creative --build` one-shot pipeline in `self_skeleton.py` (merged from `quick_batch.py`)
- `--cast-size` (auto/large/1-6), `--container` (8 vessel types), `--skip-validate` options
- `skill_doctor.py` self-diagnostic (24 checks)
- `convert_index.py` seasonal produce index converter
- `brief_history.py` brief version history tracker
- CI workflow (pytest + skill_doctor + flake8 on Python 3.10-3.12)
- Cross-platform compliance: LF line endings, shebangs, `.gitattributes`, `CHANGELOG.md`

### Changed
- **BREAKING**: Removed `external` source mode; `source` validation tightened to `"self"` only
- **BREAKING**: Removed `self-B` batch mode
- **BREAKING**: Removed HTML visualization panel (`panel/`, `panel_pro.html`, `start_panel.py`)
- **BREAKING**: Removed `quick_batch.py` (capability merged into `self_skeleton.py --build`)
- **BREAKING**: Removed fast render tier; only formal tier (5.0pro / 2048 / dual-draft) remains
- `auto-creative` latin line now requires uppercase scientific name; absent latin is skipped (no lowercase fallback)
- Unified `__version__` to `2.1.0` across all scripts
- `creative_generator.py`: fixed Chinese "结构" field leaking into English `pv_en`; added `extract_structure_size_en()`
- All text files normalized to LF line endings

### Removed
- `scripts/director_dom.py`
- `scripts/quick_batch.py`
- `references/director-contract.md`
- `references/performance-modes.md`
- `panel/` directory (panel_pro.html, start_panel.py, _run_panel.vbs, panel_config.json)

## [2.0.0] - 2026-08

### Added
- Three equal styles: S1 watercolor-crayon, S2 narrative arrangement, S3 pastel-oil-pastel grain
- brief@1.1 plan-render collaborative format
- Seasonal produce index (374 entries)
- Color palette post-processing
- Pseudo-text detection in `prep_images.py`
- Reference photo style extraction

[2.1.0]: https://github.com/your-org/still-life-illustrator-v2/releases/tag/v2.1.0
[2.0.0]: https://github.com/your-org/still-life-illustrator-v2/releases/tag/v2.0.0
