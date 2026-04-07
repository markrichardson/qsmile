## ADDED Requirements

### Requirement: SmileData accepts optional volume data
The system SHALL accept an optional `volume` parameter of type `NDArray[np.float64] | None` (default `None`) representing per-point traded volume.

#### Scenario: Construct SmileData with volume
- **WHEN** a user creates a `SmileData` with a `volume` array of the same length as `x`
- **THEN** the `volume` field SHALL be stored as a NumPy float64 array and accessible as an attribute

#### Scenario: Construct SmileData without volume
- **WHEN** a user creates a `SmileData` without providing `volume`
- **THEN** the `volume` field SHALL be `None`

#### Scenario: Volume array length mismatch rejected
- **WHEN** `volume` is provided with a different length than `x`
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Negative volume rejected
- **WHEN** any value in `volume` is negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: SmileData accepts optional open interest data
The system SHALL accept an optional `open_interest` parameter of type `NDArray[np.float64] | None` (default `None`) representing per-point open interest.

#### Scenario: Construct SmileData with open interest
- **WHEN** a user creates a `SmileData` with an `open_interest` array of the same length as `x`
- **THEN** the `open_interest` field SHALL be stored as a NumPy float64 array and accessible as an attribute

#### Scenario: Construct SmileData without open interest
- **WHEN** a user creates a `SmileData` without providing `open_interest`
- **THEN** the `open_interest` field SHALL be `None`

#### Scenario: Open interest array length mismatch rejected
- **WHEN** `open_interest` is provided with a different length than `x`
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Negative open interest rejected
- **WHEN** any value in `open_interest` is negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: SmileData transform preserves volume and open interest
The `transform()` method SHALL propagate `volume` and `open_interest` to the returned `SmileData`. Since transforms do not filter points, the arrays SHALL be copied as-is.

#### Scenario: Transform preserves volume
- **WHEN** `transform()` is called on a `SmileData` with `volume` set
- **THEN** the returned `SmileData` SHALL have the same `volume` array

#### Scenario: Transform preserves open interest
- **WHEN** `transform()` is called on a `SmileData` with `open_interest` set
- **THEN** the returned `SmileData` SHALL have the same `open_interest` array

#### Scenario: Transform preserves None volume and open interest
- **WHEN** `transform()` is called on a `SmileData` where `volume` and `open_interest` are `None`
- **THEN** the returned `SmileData` SHALL have `volume=None` and `open_interest=None`
