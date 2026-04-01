## MODIFIED Requirements

### Requirement: UnitisedSpaceVols converts back to OptionChainVols
The system SHALL provide a `to_vols(forward, strikes)` method that inverts the normalisation, converting back to `OptionChainVols`. This method SHALL be implemented as a convenience wrapper that internally constructs a `SmileData` with `(StandardisedStrike, TotalVariance)` coordinates, transforms to `(FixedStrike, Volatility)`, and unpacks the result. The user SHALL supply forward and strikes since the unitised representation discards absolute scale.

#### Scenario: Round-trip through unitised space
- **WHEN** an `OptionChainVols` is converted to `UnitisedSpaceVols` and back
- **THEN** the recovered vols SHALL match the originals within floating-point tolerance

## ADDED Requirements

### Requirement: UnitisedSpaceVols exposes SmileData
The system SHALL provide a `to_smile_data()` method on `UnitisedSpaceVols` that returns a `SmileData` with `x_coord=XCoord.StandardisedStrike`, `y_coord=YCoord.TotalVariance`, X values as k_unitised, and Y bid/ask as variance_bid and variance_ask.

#### Scenario: Construct SmileData from unitised vols
- **WHEN** `to_smile_data()` is called on a `UnitisedSpaceVols`
- **THEN** the returned `SmileData` SHALL have StandardisedStrike X-coordinates, TotalVariance Y-coordinates, and metadata populated with sigma_atm and expiry
