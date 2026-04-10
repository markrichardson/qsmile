## MODIFIED Requirements

### Requirement: SmileData stores coordinate-labelled smile data
The system SHALL provide a `SmileData` dataclass that holds `strikearray: StrikeArray`, `x_coord: XCoord`, `y_coord: YCoord`, and `metadata: SmileMetadata`. The `StrikeArray` SHALL use the strike axis as its index and store Y-axis bid/ask data as columns `("y", "bid")` and `("y", "ask")`. Optional volume and open interest SHALL be stored as `("y", "volume")` and `("y", "open_interest")` columns in the `StrikeArray`. Construction SHALL validate coordinate-specific domain invariants and require at least 3 data points.

#### Scenario: Construct SmileData with StrikeArray
- **WHEN** a user creates a `SmileData` with a populated `StrikeArray` (containing `y_bid` and `y_ask` columns), coordinate labels, and metadata
- **THEN** all fields SHALL be stored and accessible as attributes

#### Scenario: Fewer than 3 points rejected
- **WHEN** the `StrikeArray` contains fewer than 3 strikes
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Domain validation applied
- **WHEN** a `SmileData` is constructed with `x_coord=FixedStrike` and non-positive strikes in the `StrikeArray`
- **THEN** the system SHALL raise a `ValueError`

### Requirement: SmileData provides mid Y values
The system SHALL provide a `y_mid` property returning the element-wise mean of the bid and ask columns from the `StrikeArray`.

#### Scenario: Mid computation
- **WHEN** `y_mid` is accessed
- **THEN** the system SHALL return `(y_bid + y_ask) / 2` as an NDArray

### Requirement: SmileData transforms to target coordinates
The system SHALL provide a `transform(target_x: XCoord, target_y: YCoord) -> SmileData` method that returns a new `SmileData` with the data re-expressed in the target coordinate system. The returned `SmileData` SHALL use a new `StrikeArray` populated with the transformed values.

#### Scenario: Identity transform
- **WHEN** `transform()` is called with the same X and Y coordinates as the source
- **THEN** the returned SmileData SHALL contain numerically identical arrays

#### Scenario: X-only transform
- **WHEN** `transform()` is called with a different target_x but the same target_y
- **THEN** only the X values (strikes) SHALL change; Y values SHALL remain the same

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

### Requirement: SmileData accepts optional volume data
Volume SHALL be stored as a column in the `StrikeArray`. If no volume column is present, the system SHALL treat volume as absent.

#### Scenario: Construct SmileData with volume
- **WHEN** a user creates a `SmileData` whose `StrikeArray` has a volume column
- **THEN** the volume SHALL be accessible via `strikearray.values("volume")`

#### Scenario: Construct SmileData without volume
- **WHEN** a user creates a `SmileData` whose `StrikeArray` has no volume column
- **THEN** `strikearray.get_values("volume")` SHALL return `None`

#### Scenario: Negative volume rejected
- **WHEN** any value in the volume column is negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: SmileData accepts optional open interest data
Open interest SHALL be stored as a column in the `StrikeArray`. If no open interest column is present, the system SHALL treat open interest as absent.

#### Scenario: Construct SmileData with open interest
- **WHEN** a user creates a `SmileData` whose `StrikeArray` has an open_interest column
- **THEN** the open interest SHALL be accessible via `strikearray.values("open_interest")`

#### Scenario: Construct SmileData without open interest
- **WHEN** a user creates a `SmileData` whose `StrikeArray` has no open_interest column
- **THEN** `strikearray.get_values("open_interest")` SHALL return `None`

#### Scenario: Negative open interest rejected
- **WHEN** any value in the open_interest column is negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: SmileData transform preserves volume and open interest
The `transform()` method SHALL propagate volume and open interest columns to the returned `SmileData`'s `StrikeArray`. Since transforms do not filter points, the arrays SHALL be copied as-is into the new `StrikeArray`.

#### Scenario: Transform preserves volume
- **WHEN** `transform()` is called on a `SmileData` whose `StrikeArray` has a volume column
- **THEN** the returned `SmileData`'s `StrikeArray` SHALL have the same volume data

#### Scenario: Transform preserves open interest
- **WHEN** `transform()` is called on a `SmileData` whose `StrikeArray` has an open_interest column
- **THEN** the returned `SmileData`'s `StrikeArray` SHALL have the same open interest data
