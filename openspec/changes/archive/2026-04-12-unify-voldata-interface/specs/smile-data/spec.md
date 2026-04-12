## RENAMED Requirements

### Requirement: VolData coordinate fields match SmileModel naming
- **FROM:** `x_coord`, `y_coord`
- **TO:** `current_x_coord`, `current_y_coord`

## MODIFIED Requirements

### Requirement: VolData stores coordinate-labelled smile data
The system SHALL provide a `VolData` dataclass that holds `strikearray: StrikeArray`, `current_x_coord: XCoord`, `current_y_coord: YCoord`, and `metadata: SmileMetadata`. The `current_x_coord` and `current_y_coord` fields SHALL indicate the coordinate system data is currently presented in. Construction SHALL set `current_x_coord` and `current_y_coord` to the coordinates the data was originally provided in. Construction SHALL validate coordinate-specific domain invariants and require at least 3 data points.

#### Scenario: Construct VolData with current coord fields
- **WHEN** a user creates a `VolData` with a populated `StrikeArray`, coordinate labels, and metadata
- **THEN** `current_x_coord` and `current_y_coord` SHALL be accessible as attributes
- **AND** they SHALL equal the coordinates provided at construction

#### Scenario: Fewer than 3 points rejected
- **WHEN** the `StrikeArray` contains fewer than 3 strikes
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Domain validation applied
- **WHEN** a `VolData` is constructed with `current_x_coord=FixedStrike` and non-positive strikes in the `StrikeArray`
- **THEN** the system SHALL raise a `ValueError`

### Requirement: VolData transforms to target coordinates
The system SHALL provide a `transform(target_x: XCoord, target_y: YCoord) -> VolData` method that returns a new `VolData` with `current_x_coord` and `current_y_coord` set to the target values. The underlying native data SHALL NOT be physically transformed; instead, property accessors SHALL apply transforms lazily.

#### Scenario: Transform updates current coords
- **WHEN** `transform(target_x, target_y)` is called
- **THEN** the returned VolData SHALL have `current_x_coord == target_x` and `current_y_coord == target_y`

#### Scenario: Transform preserves native data
- **WHEN** `transform()` is called
- **THEN** the returned VolData's internal `StrikeArray` SHALL be unchanged

#### Scenario: Round-trip transform preserves data
- **WHEN** VolData is transformed from coordinates (A, B) to (C, D) and back to (A, B)
- **THEN** the recovered arrays from accessors SHALL match the originals within floating-point tolerance

### Requirement: VolData transform preserves volume and open interest
The `transform()` method SHALL propagate volume and open interest data to the returned `VolData`. Since the native `StrikeArray` is shared, volume and open interest SHALL be accessible on the transformed instance.

#### Scenario: Transform preserves volume
- **WHEN** `transform()` is called on a `VolData` whose `StrikeArray` has a `("meta", "volume")` column
- **THEN** the returned `VolData`'s `volume` property SHALL return the same data

#### Scenario: Transform preserves open interest
- **WHEN** `transform()` is called on a `VolData` whose `StrikeArray` has a `("meta", "open_interest")` column
- **THEN** the returned `VolData`'s `open_interest` property SHALL return the same data
