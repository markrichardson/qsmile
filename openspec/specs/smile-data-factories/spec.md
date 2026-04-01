## Requirements

### Requirement: SmileData provides from_mid_vols factory
The system SHALL provide a `SmileData.from_mid_vols(strikes, ivs, forward, expiry, discount_factor=1.0)` classmethod that returns a `SmileData` with `x_coord=XCoord.FixedStrike`, `y_coord=YCoord.Volatility`, `y_bid = y_ask = ivs` (zero spread), and metadata populated with `forward`, `discount_factor`, `expiry`, and `sigma_atm` derived from the ATM strike.

#### Scenario: Construct from mid vols
- **WHEN** `SmileData.from_mid_vols(strikes, ivs, forward, expiry)` is called with valid arrays and parameters
- **THEN** the returned `SmileData` SHALL have `x_coord=FixedStrike`, `y_coord=Volatility`, `x=strikes`, `y_bid=ivs`, `y_ask=ivs`, and metadata with auto-derived `sigma_atm`

#### Scenario: Discount factor defaults to 1.0
- **WHEN** `SmileData.from_mid_vols(strikes, ivs, forward, expiry)` is called without discount_factor
- **THEN** the returned `SmileData` SHALL have `metadata.discount_factor == 1.0`

#### Scenario: Custom discount factor
- **WHEN** `SmileData.from_mid_vols(strikes, ivs, forward, expiry, discount_factor=0.95)` is called
- **THEN** the returned `SmileData` SHALL have `metadata.discount_factor == 0.95`

#### Scenario: sigma_atm auto-derived from ATM strike
- **WHEN** `SmileData.from_mid_vols(strikes, ivs, forward, expiry)` is called
- **THEN** `metadata.sigma_atm` SHALL equal the implied vol at the strike closest to `forward`
