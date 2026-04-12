## ADDED Requirements

### Requirement: VolData stores data in native coordinates
`VolData` SHALL store its `StrikeArray` data in the coordinate system it was originally constructed with ("native coordinates"). The native coordinate system SHALL be recorded as `native_x_coord` and `native_y_coord` properties. These SHALL be immutable after construction.

#### Scenario: Native coords match construction coords
- **WHEN** a `VolData` is constructed with `x_coord=XCoord.FixedStrike` and `y_coord=YCoord.Volatility`
- **THEN** `native_x_coord` SHALL be `XCoord.FixedStrike`
- **AND** `native_y_coord` SHALL be `YCoord.Volatility`

#### Scenario: Native coords unchanged after transform
- **WHEN** `transform(XCoord.LogMoneynessStrike, YCoord.TotalVariance)` is called on a VolData with native coords `(FixedStrike, Volatility)`
- **THEN** the returned VolData's `native_x_coord` SHALL still be `XCoord.FixedStrike`
- **AND** the returned VolData's `native_y_coord` SHALL still be `YCoord.Volatility`

### Requirement: VolData transform is lightweight
`VolData.transform(target_x, target_y)` SHALL return a new `VolData` instance with `current_x_coord` and `current_y_coord` set to the target coordinates, without physically transforming the underlying data arrays. The returned instance SHALL share the same native `StrikeArray` data.

#### Scenario: Transform only changes current coord labels
- **WHEN** `transformed = data.transform(XCoord.LogMoneynessStrike, YCoord.Volatility)` is called
- **THEN** `transformed.current_x_coord` SHALL be `XCoord.LogMoneynessStrike`
- **AND** `transformed.current_y_coord` SHALL be `YCoord.Volatility`
- **AND** the underlying native `StrikeArray` SHALL be the same object as the original

#### Scenario: Chained transforms compose correctly
- **WHEN** `data.transform(A, B).transform(C, D)` is called
- **THEN** the result SHALL have `current_x_coord == C` and `current_y_coord == D`
- **AND** the underlying native data SHALL be unchanged

#### Scenario: Identity transform
- **WHEN** `data.transform(data.current_x_coord, data.current_y_coord)` is called
- **THEN** the returned VolData SHALL have identical `x`, `y_bid`, `y_ask` values

### Requirement: VolData property accessors apply lazy transforms
The `x`, `y_bid`, `y_ask`, and `y_mid` property accessors SHALL return data transformed from native coordinates to the current coordinate system. When `current_x_coord == native_x_coord` and `current_y_coord == native_y_coord`, the accessors SHALL return the native arrays directly without transformation.

#### Scenario: Accessor returns native data when coords match
- **WHEN** `data.x` is accessed and `current_x_coord == native_x_coord`
- **THEN** the returned array SHALL be the native strike array values

#### Scenario: Accessor transforms to current coords
- **WHEN** a VolData is constructed in `(FixedStrike, Volatility)` and transformed to `(LogMoneynessStrike, TotalVariance)`
- **THEN** `data.x` SHALL return log-moneyness values
- **AND** `data.y_bid` SHALL return total-variance bid values

#### Scenario: Round-trip through accessors preserves data
- **WHEN** a VolData is transformed from `(A, B)` to `(C, D)` and back to `(A, B)`
- **THEN** the `x`, `y_bid`, `y_ask` values SHALL match the original within floating-point tolerance
