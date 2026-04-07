## Requirements

### Requirement: OptionChain exposes SmileData
The system SHALL provide a `to_smile_data()` method on `OptionChain` that returns a `SmileData` with `x_coord=XCoord.FixedStrike`, `y_coord=YCoord.Price`, X values as strikes, and Y bid/ask as the call bid and ask prices. If `volume` and/or `open_interest` are present on the `OptionChain`, they SHALL be passed through to the returned `SmileData`.

#### Scenario: Construct SmileData from prices
- **WHEN** `to_smile_data()` is called on an `OptionChain`
- **THEN** the returned `SmileData` SHALL have FixedStrike X-coordinates, Price Y-coordinates, and metadata populated from the chain's forward, discount_factor, and expiry

#### Scenario: Volume and open interest passed through to SmileData
- **WHEN** `to_smile_data()` is called on an `OptionChain` with `volume` and `open_interest`
- **THEN** the returned `SmileData` SHALL have `volume` and `open_interest` arrays matching the chain's arrays

#### Scenario: None volume and open interest passed through
- **WHEN** `to_smile_data()` is called on an `OptionChain` where `volume` and `open_interest` are `None`
- **THEN** the returned `SmileData` SHALL have `volume=None` and `open_interest=None`

### Requirement: OptionChain exposes blended vol SmileData
The system SHALL provide a `to_smile_data()` method on `OptionChain` that returns a `SmileData` with `x_coord=XCoord.FixedStrike`, `y_coord=YCoord.Volatility`, X values as strikes, and Y bid/ask as delta-blended implied volatilities computed from both call and put prices. The method SHALL source `forward`, `discount_factor`, and `expiry` from `self.metadata`. It SHALL derive `sigma_atm` and produce a completed `SmileMetadata` (with `sigma_atm` populated) on the returned `SmileData`. If `volume` and/or `open_interest` are present on the `OptionChain`, they SHALL be subset to surviving strikes and passed through to the returned `SmileData`.

#### Scenario: Construct blended vol SmileData
- **WHEN** `to_smile_data()` is called on an `OptionChain` with calibrated metadata
- **THEN** the returned `SmileData` SHALL have FixedStrike X-coordinates, Volatility Y-coordinates, delta-blended bid/ask vols, and metadata populated with forward, discount_factor, expiry, and sigma_atm sourced from `self.metadata`

#### Scenario: sigma_atm auto-derived
- **WHEN** `to_smile_data()` returns a `SmileData`
- **THEN** `metadata.sigma_atm` SHALL equal the blended mid vol at the strike closest to the forward

#### Scenario: Volume and open interest subset through blended conversion
- **WHEN** `to_smile_data()` is called on an `OptionChain` with `volume` and `open_interest`
- **THEN** the returned `SmileData` SHALL have `volume` and `open_interest` arrays subset to the same valid strikes as the blended vols
