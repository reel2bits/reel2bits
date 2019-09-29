# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]
### Added
- **Breaking:** If you had installed the db previously, you might want to run `flask db migrate` and then the following db-datas migrations:
    - 001-generate-tracks-uuids
    - 002-set-local-users
    - 003-set-user-quota
    - 004-update-file-sizes
- **Breaking:** Commands to run: `flask db-datas 005-update-user-quotas` to precompute the user quotas
- User quotas
