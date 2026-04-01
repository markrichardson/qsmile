## MODIFIED Requirements

### Requirement: OptionChainPrices converts to OptionChainVols
The system SHALL provide a `to_vols()` method that converts the price chain to an `OptionChainVols` by inverting bid and ask prices through Black76. This method SHALL be implemented as a convenience wrapper that internally constructs a `SmileData` with `(FixedStrike, Price)` coordinates, transforms to `(FixedStrike, Volatility)`, and unpacks the result.

#### Scenario: Vol conversion produces correct result
- **WHEN** `to_vols()` is called on an `OptionChainPrices`
- **THEN** the returned `OptionChainVols` SHALL contain Black76-inverted implied volatilities matching the existing behaviour

#### Scenario: Round-trip through prices and vols
- **WHEN** an `OptionChainPrices` is converted to vols via `to_vols()` and back via `to_prices()`
- **THEN** the recovered prices SHALL match the originals within floating-point tolerance

## ADDED Requirements

### Requirement: OptionChainPrices exposes SmileData
The system SHALL provide a `to_smile_data()` method on `OptionChainPrices` that returns a `SmileData` with `x_coord=XCoord.FixedStrike`, `y_coord=YCoord.Price`, X values as strikes, and Y bid/ask as the call mid-market prices (bid and ask).

#### Scenario: Construct SmileData from prices
- **WHEN** `to_smile_data()` is called on an `OptionChainPrices`
- **THEN** the returned `SmileData` SHALL have FixedStrike X-coordinates, Price Y-coordinates, and metadata populated from the chain's forward, discount_factor, and expiry
