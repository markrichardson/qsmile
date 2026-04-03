## Requirements

### Requirement: OptionChain exposes SmileData
The system SHALL provide a `to_smile_data()` method on `OptionChain` that returns a `SmileData` with `x_coord=XCoord.FixedStrike`, `y_coord=YCoord.Price`, X values as strikes, and Y bid/ask as the call bid and ask prices. This is the sole conversion method on `OptionChain`.

#### Scenario: Construct SmileData from prices
- **WHEN** `to_smile_data()` is called on an `OptionChain`
- **THEN** the returned `SmileData` SHALL have FixedStrike X-coordinates, Price Y-coordinates, and metadata populated from the chain's forward, discount_factor, and expiry
