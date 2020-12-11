# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## 0.1.0b2 - 2020-12-11

Blueprint Locations!

### Added

- Location resolution and display for blueprints
- Mechanism to update swagger.json (`make update_swagger`)
- Management command to update all blueprints and locations

### Changed

- Updated swagger from latest EVE API
- Switched to decorators for fetching tokens in the `Owner` model

## 0.1.0b1 - 2020-12-09

Transifex support

### Added

- Transifex config / support commands to Makefile

## 0.1.0a3 - 2020-12-06

Pagination fix

### Fixed

- Fixed pagination bug

## 0.1.0a2 - 2020-12-06

Small fixes

### Added

- Model help text refined
- Admin interface improved
  - Blueprints are now read-only
  - Blueprints are now searchable and display additional information on the list page.
- Increased recommended update interval to 3 hours

## 0.1.0a1 - 2020-12-06

Initial Alpha

### Added

- i18n support
- Management command to download blueprint types

## 0.1.0.dev2 - 2020-12-06

### Changed

- Removed default permissions for Location and Blueprint models

## 0.1.0.dev1 - 2020-12-06

Initial Dev Release
