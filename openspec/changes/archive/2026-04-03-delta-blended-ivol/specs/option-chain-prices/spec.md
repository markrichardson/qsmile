## MODIFIED Requirements

### Requirement: OptionChain exposes SmileData
The system SHALL provide a `to_smile_data()` method on `OptionChain` that returns a `SmileData` with `x_coord=XCoord.FixedStrike`, `y_coord=YCoord.Price`, X values as strikes, and Y bid/ask as the call bid and ask prices. This is the price-based conversion method on `OptionChain`.

#### Scenario: Construct SmileData from prices
- **WHEN** `to_smile_data()` is called on an `OptionChain`
- **THEN** the returned `SmileData` SHALL have FixedStrike X-coordinates, Price Y-coordinates, and metadata populated from the chain's forward, discount_factor, and expiry

## ADDED Requirements

### Requirement: OptionChain exposes blended vol SmileData
The system SHALL provide a `to_smile_data_blended()` method on `OptionChain` that returns a `SmileData` with `x_coord=XCoord.FixedStrike`, `y_coord=YCoord.Volatility`, X values as strikes, and Y bid/ask as delta-blended implied volatilities computed from both call and put prices.

#### Scenario: Construct blended vol SmileData
- **WHEN** `to_smile_data_blended()` is called on an `OptionChain` with calibrated forward and discount factor
- **THEN** the returned `SmileData` SHALL have FixedStrike X-coordinates, Volatility Y-coordinates, delta-blended bid/ask vols, and metadata populated with forward, discount_factor, expiry, and sigma_atm

#### Scenario: Blended method requires calibration
- **WHEN** `to_smile_data_blended()` is called on an `OptionChain` without calibrated forward/discount_factor
- **THEN** the system SHALL raise an error (same precondition as `to_smile_data()`)

#### Scenario: sigma_atm auto-derived
- **WHEN** `to_smile_data_blended()` returns a `SmileData`
- **THEN** `metadata.sigma_atm` SHALL equal the blended mid vol at the strike closest to the forward
