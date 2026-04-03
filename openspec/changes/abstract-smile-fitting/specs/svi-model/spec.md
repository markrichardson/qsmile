## MODIFIED Requirements

### Requirement: SVIParams represents raw SVI parameters
The system SHALL provide an `SVIParams` dataclass with fields `a`, `b`, `rho`, `m`, and `sigma` representing the five raw SVI parameters. `SVIParams` SHALL also conform to the `SmileModel` protocol.

#### Scenario: Create SVIParams
- **WHEN** a user constructs `SVIParams(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)`
- **THEN** all five parameters are stored and accessible as attributes

#### Scenario: SVIParams conforms to SmileModel
- **WHEN** an `SVIParams` instance is checked against the `SmileModel` protocol
- **THEN** the check SHALL pass (all required methods/properties are present)

### Requirement: SVIParams declares SVI native coordinates
`SVIParams` SHALL expose `native_x_coord` returning `XCoord.LogMoneynessStrike` and `native_y_coord` returning `YCoord.TotalVariance`.

#### Scenario: Access native coordinates
- **WHEN** `native_x_coord` and `native_y_coord` are accessed on an `SVIParams` instance
- **THEN** they SHALL return `XCoord.LogMoneynessStrike` and `YCoord.TotalVariance`

### Requirement: SVIParams provides parameter serialisation
`SVIParams` SHALL implement `to_array()` returning `[a, b, rho, m, sigma]` and `from_array(x)` reconstructing an `SVIParams` from a flat array.

#### Scenario: Round-trip serialisation
- **WHEN** `SVIParams.from_array(params.to_array())` is called
- **THEN** the resulting `SVIParams` SHALL have the same field values

### Requirement: SVIParams provides bounds
`SVIParams` SHALL expose a `bounds` property returning `([-inf, 0.0, -0.999, -inf, 1e-8], [inf, inf, 0.999, inf, inf])`.

#### Scenario: Bounds match SVI constraints
- **WHEN** `bounds` is accessed
- **THEN** the lower/upper bounds SHALL enforce $b \geq 0$, $-1 < \rho < 1$, $\sigma > 0$

### Requirement: SVIParams provides evaluation
`SVIParams` SHALL implement `evaluate(x)` that computes SVI total variance $w(k) = a + b(\rho(k - m) + \sqrt{(k - m)^2 + \sigma^2})$.

#### Scenario: Evaluate matches svi_total_variance
- **WHEN** `params.evaluate(k)` is called
- **THEN** the result SHALL be identical to `svi_total_variance(k, params)`

### Requirement: SVIParams provides initial guess
`SVIParams` SHALL implement `initial_guess(x, y)` as a static/class method that computes a heuristic starting point from log-moneyness and total-variance arrays.

#### Scenario: Initial guess returns 5-element array
- **WHEN** `SVIParams.initial_guess(k, w)` is called with market data
- **THEN** the result SHALL be a 5-element NumPy array
