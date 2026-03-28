## ADDED Requirements

### Requirement: UnitisedSpaceVols represents vols in normalised coordinates
The system SHALL provide a `UnitisedSpaceVols` dataclass that holds the smile in unitised coordinates: $\tilde{k} = \log(K/F) / (\sigma_{\text{ATM}} \sqrt{t})$ (unitised log-moneyness) and $v = \sigma_k^2 \, t$ (total variance). Both bid and ask total variances SHALL be stored.

#### Scenario: Construct UnitisedSpaceVols
- **WHEN** a user creates a `UnitisedSpaceVols` with arrays of unitised log-moneyness, total variance bid, total variance ask, sigma_atm, and expiry
- **THEN** all fields SHALL be stored and accessible as attributes

### Requirement: UnitisedSpaceVols validates inputs
The system SHALL validate unitised space data on construction.

#### Scenario: Mismatched array lengths
- **WHEN** variance arrays have a different length from the unitised log-moneyness array
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Negative total variance
- **WHEN** any total variance value is negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Bid exceeds ask
- **WHEN** any total variance bid exceeds the corresponding ask
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive sigma_atm
- **WHEN** sigma_atm is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive expiry
- **WHEN** expiry is zero or negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: UnitisedSpaceVols provides mid total variance
The system SHALL provide a `variance_mid` property returning the midpoint of bid and ask total variances.

#### Scenario: Mid variance computation
- **WHEN** `variance_mid` is accessed
- **THEN** the system SHALL return `(variance_bid + variance_ask) / 2`

### Requirement: UnitisedSpaceVols converts back to OptionChainVols
The system SHALL provide a `to_vols(forward, strikes)` method that inverts the normalisation, converting back to `OptionChainVols`. The user SHALL supply forward and strikes since the unitised representation discards absolute scale.

#### Scenario: Round-trip through unitised space
- **WHEN** an `OptionChainVols` is converted to `UnitisedSpaceVols` and back
- **THEN** the recovered vols SHALL match the originals within floating-point tolerance
