## ADDED Requirements

### Requirement: X-coordinate maps between adjacent coordinate types
The system SHALL provide forward and inverse map functions for each adjacent pair in the X-coordinate ladder: `FixedStrike ↔ MoneynessStrike ↔ LogMoneynessStrike ↔ StandardisedStrike`. Each map SHALL accept an NDArray and a SmileMetadata and return a transformed NDArray.

#### Scenario: FixedStrike to MoneynessStrike
- **WHEN** the FixedStrike→MoneynessStrike map is applied to strikes K with metadata containing forward F
- **THEN** the result SHALL be K / F

#### Scenario: MoneynessStrike to FixedStrike
- **WHEN** the MoneynessStrike→FixedStrike map is applied to moneyness m with metadata containing forward F
- **THEN** the result SHALL be m * F

#### Scenario: MoneynessStrike to LogMoneynessStrike
- **WHEN** the MoneynessStrike→LogMoneynessStrike map is applied to moneyness m
- **THEN** the result SHALL be ln(m)

#### Scenario: LogMoneynessStrike to MoneynessStrike
- **WHEN** the LogMoneynessStrike→MoneynessStrike map is applied to log-moneyness k
- **THEN** the result SHALL be exp(k)

#### Scenario: LogMoneynessStrike to StandardisedStrike
- **WHEN** the LogMoneynessStrike→StandardisedStrike map is applied to log-moneyness k with metadata containing sigma_atm and expiry T
- **THEN** the result SHALL be k / (sigma_atm * sqrt(T))

#### Scenario: StandardisedStrike to LogMoneynessStrike
- **WHEN** the StandardisedStrike→LogMoneynessStrike map is applied to standardised strike s with metadata containing sigma_atm and expiry T
- **THEN** the result SHALL be s * sigma_atm * sqrt(T)

#### Scenario: X-map round-trip preserves values
- **WHEN** any X forward map is applied followed by its inverse
- **THEN** the result SHALL match the original values within floating-point tolerance

### Requirement: Y-coordinate maps between adjacent coordinate types
The system SHALL provide forward and inverse map functions for each adjacent pair in the Y-coordinate ladder: `Price ↔ Volatility ↔ Variance ↔ TotalVariance`. Each map SHALL accept Y-arrays, X-arrays (in appropriate coordinates), and SmileMetadata, and return transformed Y-arrays.

#### Scenario: Volatility to Variance
- **WHEN** the Volatility→Variance map is applied to implied volatilities σ
- **THEN** the result SHALL be σ²

#### Scenario: Variance to Volatility
- **WHEN** the Variance→Volatility map is applied to variances v
- **THEN** the result SHALL be sqrt(v)

#### Scenario: Variance to TotalVariance
- **WHEN** the Variance→TotalVariance map is applied to variances v with metadata containing expiry T
- **THEN** the result SHALL be v * T

#### Scenario: TotalVariance to Variance
- **WHEN** the TotalVariance→Variance map is applied to total variances w with metadata containing expiry T
- **THEN** the result SHALL be w / T

#### Scenario: Volatility to Price (forward direction)
- **WHEN** the Volatility→Price map is applied to implied volatilities with X in FixedStrike coordinates
- **THEN** the result SHALL be Black76 option prices computed using the strikes, forward, discount factor, and expiry from metadata

#### Scenario: Price to Volatility (inverse direction)
- **WHEN** the Price→Volatility map is applied to option prices with X in FixedStrike coordinates
- **THEN** the result SHALL be Black76 implied volatilities computed via numerical inversion

#### Scenario: Price↔Volatility requires FixedStrike X-coordinates
- **WHEN** the Price↔Volatility map is requested and X-coordinates are not in FixedStrike
- **THEN** the system SHALL first transform X to FixedStrike, apply the map, then transform X back

#### Scenario: Y-map round-trip preserves values
- **WHEN** any Y forward map is applied followed by its inverse
- **THEN** the result SHALL match the original values within floating-point tolerance

### Requirement: Coordinate map composition
The system SHALL provide a function that, given a source and target coordinate (X or Y), returns the composed chain of maps needed to transform between them by walking the coordinate ladder.

#### Scenario: Adjacent coordinates require one map
- **WHEN** the source and target are adjacent on the ladder (e.g., Volatility→Variance)
- **THEN** the composed chain SHALL contain exactly one map step

#### Scenario: Non-adjacent coordinates require multiple maps
- **WHEN** the source and target are separated by N steps on the ladder (e.g., FixedStrike→StandardisedStrike = 3 steps)
- **THEN** the composed chain SHALL contain exactly N map steps applied in order

#### Scenario: Same coordinate requires no maps
- **WHEN** the source and target are the same coordinate
- **THEN** the composed chain SHALL be the identity (no transformation applied)
