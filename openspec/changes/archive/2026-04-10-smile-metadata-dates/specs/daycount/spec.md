## ADDED Requirements

### Requirement: DayCount enum defines day-count conventions
The system SHALL provide a `DayCount` enum in `src/qsmile/core/daycount.py` with variants `ACT365` and `ACT360`. Each variant SHALL have a `year_fraction(start, end)` method that computes the year fraction between two `pd.Timestamp` values.

#### Scenario: ACT365 year fraction
- **WHEN** `DayCount.ACT365.year_fraction(start, end)` is called with two dates 365 days apart
- **THEN** the result SHALL be `1.0`

#### Scenario: ACT360 year fraction
- **WHEN** `DayCount.ACT360.year_fraction(start, end)` is called with two dates 360 days apart
- **THEN** the result SHALL be `1.0`

#### Scenario: ACT365 fractional year
- **WHEN** `DayCount.ACT365.year_fraction(start, end)` is called with two dates 91 days apart
- **THEN** the result SHALL be `91 / 365.0`

#### Scenario: ACT360 fractional year
- **WHEN** `DayCount.ACT360.year_fraction(start, end)` is called with two dates 91 days apart
- **THEN** the result SHALL be `91 / 360.0`

#### Scenario: Same-day year fraction
- **WHEN** `DayCount.ACT365.year_fraction(start, end)` is called with `start == end`
- **THEN** the result SHALL be `0.0`
