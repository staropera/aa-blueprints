# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## 1.0.0 - 2020-12-18

### Added

- Ability to add personal blueprints

### Changed

- Reworked object model for better flexibility and performance
- Permissions moved to Blueprints >> General to avoid confusion

## 0.2.1 - 2020-12-18

### Changed

- Improved styling

### Fixed

- Ability to see blueprint request button without permissions
- Permission error viewing blueprint requests

## 0.2.0 - 2020-12-17

### Added

- Ability to request blueprint copies

### Fixed

- Added dependency on recent versions of celery to avoid issues with tasks

## 0.1.1 - 2020-12-14

### Fixed

- Small bug in Owner object

## 0.1.0 - 2020-12-14

### Fixed

- Removed debugging code

## 0.1.0b4 - 2020-12-14

### Added

- Quantity field to blueprint table

### Changed

- Abbreviated material / time efficiency headings to allow for more compact table layout

## 0.1.0b3 - 2020-12-13

Bugfixes and tweaks

### Added

- Filter to blueprint table

### Fixed

- Re-added some error handling code that shouldn't have been removed
- Usage of bootstrap classes
- Blueprint table header classes
- Menu icon was still using the old FA library, now it isn't

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
