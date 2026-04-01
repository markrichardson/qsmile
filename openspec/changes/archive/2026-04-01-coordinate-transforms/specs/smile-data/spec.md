## ADDED Requirements

### Requirement: SmileData stores coordinate-labelled smile data
The system SHALL provide a `SmileData` dataclass that holds `x` (NDArray), `y_bid` (NDArray), `y_ask` (NDArray), `x_coord` (XCoord), `y_coord` (YCoord), and `metadata` (SmileMetadata). All array fields SHALL be NumPy float64 arrays of the same length.

#### Scenario: Construct SmileData
- **WHEN** a user creates a `SmileData` with valid arrays, coordinate labels, and metadata
- **THEN** all fields SHALL be stored and accessible as attributes

#### Scenario: Mismatched array lengths rejected
- **WHEN** y_bid or y_ask has a different length from x
- **THEN** the system SHALL raise a `ValueError`

### Requirement: SmileData provides mid Y values
The system SHALL provide a `y_mid` property returning `(y_bid + y_ask) / 2`.

#### Scenario: Mid computation
- **WHEN** `y_mid` is accessed
- **THEN** the system SHALL return the element-wise mean of y_bid and y_ask

### Requirement: SmileData transforms to target coordinates
The system SHALL provide a `transform(target_x: XCoord, target_y: YCoord) -> SmileData` method that returns a new `SmileData` with the data re-expressed in the target coordinate system.

#### Scenario: Identity transform
- **WHEN** `transform()` is called with the same X and Y coordinates as the source
- **THEN** the returned SmileData SHALL contain numerically identical arrays

#### Scenario: X-only transform
- **WHEN** `transform()` is called with a different target_x but the same target_y
- **THEN** only the X values SHALL change; Y values SHALL remain the same

#### Scenario: Y-only transform
- **WHEN** `transform()` is called with the same target_x but a different target_y
- **THEN** only the Y values SHALL change; X values SHALL remain the same

#### Scenario: Combined X and Y transform
- **WHEN** `transform()` is called with different target_x and target_y
- **THEN** both X and Y values SHALL be transformed to the target coordinate system

#### Scenario: Round-trip transform preserves data
- **WHEN** SmileData is transformed from coordinates (A, B) to (C, D) and back to (A, B)
- **THEN** the recovered arrays SHALL match the originals within floating-point tolerance

#### Scenario: Transform requiring sigma_atm without it raises error
- **WHEN** a transform to or from `StandardisedStrike` is requested and metadata.sigma_atm is None
- **THEN** the system SHALL raise a `ValueError` with a clear message
