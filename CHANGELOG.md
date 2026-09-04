# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-09-04

### Added
- Full feature set: external LLM collaboration mode (`director_dom.py`, `director-contract.md`)
- self-B batch mode (multi-subject batch with independent creative filling)
- HTML visualization panel (`panel/panel_pro.html`, `panel/start_panel.py`, `_run_panel.vbs`)
- Performance render tiers (fast / formal) via `performance-modes.md`
- `--auto-creative --build` one-shot pipeline in `self_skeleton.py`
- `--cast-size`, `--container`, `--skip-validate` options
- `skill_doctor.py` self-diagnostic
- `convert_index.py`, `brief_history.py` utilities
- CI workflow, cross-platform compliance (LF, shebangs, `.gitattributes`)

### Changed
- `auto-creative` latin line requires uppercase scientific name; absent latin is skipped
- Unified `__version__` to `3.0.0` across all scripts
- All text files normalized to LF line endings
- `build_from_brief.py`: fixed Chinese structure field leaking into English `pv_en`

### Notes
- This is the full edition. A lightweight v2.1.0 edition (without panel/external/self-B) is available at the v2.1.0 tag.

## [2.0.0] - 2026-08

### Added
- Three equal styles: S1 watercolor-crayon, S2 narrative arrangement, S3 pastel-oil-pastel grain
- brief@1.1 plan-render collaborative format
- Seasonal produce index (374 entries)
- Color palette post-processing
- Pseudo-text detection in `prep_images.py`

[3.0.0]: https://github.com/your-org/still-life-illustrator/releases/tag/v3.0.0
[2.0.0]: https://github.com/your-org/still-life-illustrator/releases/tag/v2.0.0
