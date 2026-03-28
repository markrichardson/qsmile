## ADDED Requirements

### Requirement: SVIParams represents raw SVI parameters
The system SHALL provide an `SVIParams` dataclass with fields `a`, `b`, `rho`, `m`, and `sigma` representing the five raw SVI parameters.

#### Scenario: Create SVIParams
- **WHEN** a user constructs `SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)`
- **THEN** all five parameters are stored and accessible as attributes

### Requirement: SVIParams validates parameter constraints
The system SHALL enforce the standard SVI parameter constraints on construction.

#### Scenario: Negative b
- **WHEN** `b` is negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Rho out of range
- **WHEN** `rho` is not in the open interval $(-1, 1)$
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive sigma
- **WHEN** `sigma` is zero or negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: SVI total variance evaluation
The system SHALL provide a function `svi_total_variance(k, params)` that computes total implied variance $w(k) = a + b(\rho(k - m) + \sqrt{(k - m)^2 + \sigma^2})$ for given log-moneyness values and SVI parameters.

#### Scenario: Evaluate at single log-moneyness
- **WHEN** `svi_total_variance` is called with a scalar `k` and valid `SVIParams`
- **THEN** the function SHALL return the total variance as a float

#### Scenario: Evaluate at array of log-moneyness values
- **WHEN** `svi_total_variance` is called with a NumPy array of `k` values
- **THEN** the function SHALL return a NumPy array of total variances with the same shape

#### Scenario: Symmetry at the money when rho is zero
- **WHEN** `rho = 0` and `k` values are symmetric around `m`
- **THEN** the resulting total variances SHALL be equal for $k = m + \delta$ and $k = m - \delta$

### Requirement: SVI implied volatility evaluation
The system SHALL provide a function `svi_implied_vol(k, params, expiry)` that converts total variance to implied volatility via $\sigma_{IV} = \sqrt{w(k) / T}$.

#### Scenario: Convert total variance to implied vol
- **WHEN** `svi_implied_vol` is called with valid parameters and a positive expiry
- **THEN** the function SHALL return implied volatilities as $\sqrt{w(k) / T}$

#### Scenario: Non-positive expiry
- **WHEN** expiry is zero or negative
- **THEN** the function SHALL raise a `ValueError`
