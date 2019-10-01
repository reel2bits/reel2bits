# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]
### Added
- **Breaking:** If you had installed the db previously, you might want to run `flask db migrate` and then the following db-datas migrations:
    - 000-seeds
    - 001-generate-tracks-uuids
    - 002-set-local-users
    - 003-set-user-quota
    - 004-update-file-sizes
- **Breaking:** Commands to run: `flask db-datas 005-update-user-quotas` to precompute the user quotas
- User quotas (#179)
- Refactored the cli commands (#179)
- Added a few more users commands (#184)
- Frontend now display correctly a not-ready track
- Add button to retry transcoding/processing if failed

### Changed
- PNG waveforms are not computed anymore because unused (#179)

### Fixed
- Waveform JSON generation through a .dat now use the right pixels per second; avoid huge waveforms datas for long tracks (#179)
