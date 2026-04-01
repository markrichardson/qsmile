## ADDED Requirements

### Requirement: XCoord enum defines X-coordinate types
The system SHALL provide an `XCoord` enum with members `FixedStrike`, `MoneynessStrike`, `LogMoneynessStrike`, and `StandardisedStrike`.

#### Scenario: Enumerate X-coordinate types
- **WHEN** a user accesses `XCoord` members
- **THEN** the system SHALL expose exactly four members: `FixedStrike`, `MoneynessStrike`, `LogMoneynessStrike`, `StandardisedStrike`

#### Scenario: XCoord members are distinct
- **WHEN** comparing any two different XCoord members
- **THEN** they SHALL not be equal

### Requirement: YCoord enum defines Y-coordinate types
The system SHALL provide a `YCoord` enum with members `Price`, `Volatility`, `Variance`, and `TotalVariance`.

#### Scenario: Enumerate Y-coordinate types
- **WHEN** a user accesses `YCoord` members
- **THEN** the system SHALL expose exactly four members: `Price`, `Volatility`, `Variance`, `TotalVariance`

#### Scenario: YCoord members are distinct
- **WHEN** comparing any two different YCoord members
- **THEN** they SHALL not be equal
