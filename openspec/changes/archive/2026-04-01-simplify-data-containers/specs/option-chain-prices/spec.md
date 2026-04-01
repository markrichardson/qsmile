## REMOVED Requirements

### Requirement: OptionChainPrices converts to OptionChainVols
**Reason**: `OptionChainVols` is removed. The `to_vols()` method was already removed in a prior change. This spec delta is no longer applicable.
**Migration**: Use `prices.to_smile_data().transform(XCoord.FixedStrike, YCoord.Volatility)` to obtain implied volatilities as a `SmileData`.

## MODIFIED Requirements

### Requirement: OptionChainPrices exposes SmileData
The system SHALL provide a `to_smile_data()` method on `OptionChainPrices` that returns a `SmileData` with `x_coord=XCoord.FixedStrike`, `y_coord=YCoord.Price`, X values as strikes, and Y bid/ask as the call bid and ask prices. This is the sole conversion method on `OptionChainPrices`.

#### Scenario: Construct SmileData from prices
- **WHEN** `to_smile_data()` is called on an `OptionChainPrices`
- **THEN** the returned `SmileData` SHALL have FixedStrike X-coordinates, Price Y-coordinates, and metadata populated from the chain's forward, discount_factor, and expiry
