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
    - 005-update-user-quotas
    - 006-generate-albums-uuids
- **Breaking:** Commands to run: `flask db-datas 005-update-user-quotas` to precompute the user quotas
- **Breaking:** New config options to set:
    - `UPLOADED_ARTWORKALBUMS_DEST`
    - `UPLOADED_ARTWORKSOUNDS_DEST`
    - `UPLOADED_AVATARS_DEST`
    - Update nginx config accordingly
- User quotas (#179)
- Refactored the cli commands (#179)
- Added a few more users commands (#184)
- Frontend now display correctly a not-ready track
- Add button to retry transcoding/processing if failed
- User profile now have an unprocessed tab listing thoses tracks
- Turkish language added
- An user can now delete his own account, triggering the right deletions and AP broadcasts
- Added `/.well-known/host-meta` and `/api/v1/instance` for more mastodon API compatibility
- Albums and Tracks can now have a custom artwork
- Users can now choose an avatar
- OEmbed, meta tags, Twitter Card and OpenGraph
- `flask test-email` command to send a test email
- Setting `SENTRY_DSN` in backend will activate Sentry in frontend
- There is now an admin setting for a static announcement
- CLI command to regenerate a specific waveform or all
- Max file upload size can now be overriden in config

### Changed
- PNG waveforms are not computed anymore because unused (#179)
- Timelines now uses a `paginated=true/false` GET parameter, if false, the timeline is rendered unpaginated for mastoapi compatibility
- Old unused APIToken table removed
- User language setting in profile now override browser one
- URL scheme generation should be more robust
- Added Icon(avatar) to Actor to make avatar federate
- `flask users list` command now show confirmed at field
- Quotas and file sizes are now BigInt
- Waveform generation now use dynamic PixelsPerSecond depending of the track duration
- Waveform generation now rounds the peaks to two digits
- Remote Actor now have an associated User

### Fixed
- Waveform JSON generation through a .dat now use the right pixels per second; avoid huge waveforms datas for long tracks (#179)
- Flake ID generation have been rewritten and should be good now
