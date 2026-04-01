## MODIFIED Requirements

### Requirement: SmileData stores coordinate-labelled smile data
The system SHALL provide a `SmileData` dataclass that holds `x` (NDArray), `y_bid` (NDArray), `y_ask` (NDArray), `x_coord` (XCoord), `y_coord` (YCoord), and `metadata` (SmileMetadata). All array fields SHALL be NumPy float64 arrays of the same length. Construction SHALL validate coordinate-specific domain invariants (see smile-data-validation spec) and require at least 3 data points.

#### Scenario: Construct SmileData
- **WHEN** a user creates a `SmileData` with valid arrays, coordinate labels, and metadata
- **THEN** all fields SHALL be stored and accessible as attributes

#### Scenario: Mismatched array lengths rejected
- **WHEN** y_bid or y_ask has a different length from x
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Domain validation applied
- **WHEN** a `SmileData` is constructed with `x_coord=FixedStrike` and non-positive x values
- **THEN** the system SHALL raise a `ValueError`
