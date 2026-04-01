## MODIFIED Requirements

### Requirement: OptionChainVols converts to UnitisedSpaceVols
The system SHALL provide a `to_unitised()` method that converts the vol chain to `UnitisedSpaceVols` using the normalised coordinates $\tilde{k} = \log(K/F) / (\sigma_{\text{ATM}} \sqrt{t})$ and $v = \sigma_k^2 \, t$. This method SHALL be implemented as a convenience wrapper that internally constructs a `SmileData` with `(FixedStrike, Volatility)` coordinates, transforms to `(StandardisedStrike, TotalVariance)`, and unpacks the result.

#### Scenario: Unitised conversion
- **WHEN** `to_unitised()` is called
- **THEN** the system SHALL return a `UnitisedSpaceVols` with correctly normalised coordinates for both bid and ask

### Requirement: OptionChainVols converts to prices
The system SHALL provide a `to_prices()` method that converts vol chain back to an `OptionChainPrices` using Black76 pricing. This method SHALL be implemented as a convenience wrapper that internally constructs a `SmileData` with `(FixedStrike, Volatility)` coordinates, transforms to `(FixedStrike, Price)`, and unpacks the result.

#### Scenario: Vol to price round-trip
- **WHEN** an `OptionChainPrices` is converted to vols via `to_vols()` and back via `to_prices()`
- **THEN** the recovered prices SHALL match the originals within floating-point tolerance

## ADDED Requirements

### Requirement: OptionChainVols exposes SmileData
The system SHALL provide a `to_smile_data()` method on `OptionChainVols` that returns a `SmileData` with `x_coord=XCoord.FixedStrike`, `y_coord=YCoord.Volatility`, X values as strikes, and Y bid/ask as vol_bid and vol_ask.

#### Scenario: Construct SmileData from vols
- **WHEN** `to_smile_data()` is called on an `OptionChainVols`
- **THEN** the returned `SmileData` SHALL have FixedStrike X-coordinates, Volatility Y-coordinates, and metadata populated from the chain's forward, discount_factor, expiry, and sigma_atm
