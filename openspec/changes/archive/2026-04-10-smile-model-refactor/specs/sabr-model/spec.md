## MODIFIED Requirements

### Requirement: SABRModel represents SABR parameters
The system SHALL provide a `SABRModel` dataclass with fitted fields `alpha`, `beta`, `rho`, `nu` representing the SABR stochastic volatility model. Context fields `expiry` and `forward` SHALL be removed as direct fields — they are provided via `metadata: SmileMetadata` inherited from `AbstractSmileModel`. `SABRModel` SHALL conform to the `SmileModel` protocol.

#### Scenario: Create SABRModel with metadata
- **WHEN** a user constructs `SABRModel(alpha=0.2, beta=0.5, rho=-0.3, nu=0.4, metadata=meta)` where `meta` contains expiry and forward
- **THEN** the four fitted fields and metadata are stored and accessible as attributes
- **AND** `metadata.texpiry` provides the time to expiry
- **AND** `metadata.forward` provides the forward price

#### Scenario: SABRModel conforms to SmileModel
- **WHEN** a `SABRModel` instance is checked against the `SmileModel` protocol
- **THEN** the check SHALL pass (all required methods/properties are present)

### Requirement: SABRModel validates parameter constraints
`SABRModel` SHALL validate on construction: `alpha > 0`, `0 <= beta <= 1`, `-1 < rho < 1`, `nu >= 0`.

#### Scenario: Negative alpha rejected
- **WHEN** a user constructs `SABRModel(alpha=-0.1, beta=0.5, rho=-0.3, nu=0.4, metadata=meta)`
- **THEN** a `ValueError` SHALL be raised with a message containing "alpha"

#### Scenario: Beta out of range rejected
- **WHEN** a user constructs `SABRModel(alpha=0.2, beta=1.5, rho=-0.3, nu=0.4, metadata=meta)`
- **THEN** a `ValueError` SHALL be raised with a message containing "beta"

#### Scenario: Rho out of range rejected
- **WHEN** a user constructs `SABRModel(alpha=0.2, beta=0.5, rho=1.0, nu=0.4, metadata=meta)`
- **THEN** a `ValueError` SHALL be raised with a message containing "rho"

#### Scenario: Nu zero is valid
- **WHEN** a user constructs `SABRModel(alpha=0.2, beta=0.5, rho=-0.3, nu=0.0, metadata=meta)`
- **THEN** the instance SHALL be created successfully with `nu == 0.0`

### Requirement: SABRModel declares SABR native coordinates
`SABRModel` SHALL expose `native_x_coord` returning `XCoord.LogMoneynessStrike` and `native_y_coord` returning `YCoord.Volatility`.

#### Scenario: Access native coordinates
- **WHEN** `native_x_coord` and `native_y_coord` are accessed on a `SABRModel`
- **THEN** they SHALL return `XCoord.LogMoneynessStrike` and `YCoord.Volatility`

### Requirement: SABRModel provides parameter serialisation
`SABRModel` SHALL serialise only its fitted parameters `(alpha, beta, rho, nu)` via `to_array()` and `from_array()`. `from_array` SHALL accept metadata.

#### Scenario: to_array returns 4-element array
- **WHEN** `to_array()` is called on a `SABRModel` instance
- **THEN** the result SHALL be a 4-element NumPy array `[alpha, beta, rho, nu]`

#### Scenario: Round-trip serialisation
- **WHEN** `SABRModel.from_array(model.to_array(), metadata=model.metadata)` is called
- **THEN** the resulting `SABRModel` SHALL have the same fitted parameter values and metadata

### Requirement: SABRModel provides bounds
`SABRModel` SHALL expose a `bounds` class variable constraining: `alpha > 0`, `0 <= beta <= 1`, `-1 < rho < 1`, `nu >= 0`.

#### Scenario: Bounds length matches param_names
- **WHEN** `bounds` is accessed on `SABRModel`
- **THEN** both lower and upper lists SHALL have length 4, matching `param_names`

### Requirement: SABRModel provides Hagan implied vol evaluation
`SABRModel` SHALL implement `evaluate(x)` using Hagan et al. (2002) lognormal implied volatility approximation, where `x` is log-moneyness and the result is implied volatility. The method SHALL read `expiry` and `forward` from `self.metadata`.

#### Scenario: Evaluate at ATM
- **WHEN** `evaluate(0.0)` is called (ATM, log-moneyness = 0)
- **THEN** the result SHALL be a finite positive implied volatility

#### Scenario: Evaluate at array of strikes
- **WHEN** `evaluate(k)` is called with a NumPy array of log-moneyness values
- **THEN** the result SHALL be a NumPy array of the same length containing positive implied volatilities

### Requirement: SABRModel provides initial guess
`SABRModel` SHALL implement `initial_guess(x, y)` as a static method that computes a heuristic starting point from log-moneyness and implied-volatility arrays.

#### Scenario: Initial guess returns 4-element array
- **WHEN** `SABRModel.initial_guess(k, iv)` is called with market data
- **THEN** the result SHALL be a 4-element NumPy array

#### Scenario: Initial guess within bounds
- **WHEN** `SABRModel.initial_guess(k, iv)` is called
- **THEN** each element SHALL be within the corresponding `bounds` range

### Requirement: SABRModel supports transform and __call__
`SABRModel` SHALL inherit `transform()`, `__call__()`, `plot()`, and `params` from `AbstractSmileModel`.

#### Scenario: Transform SABR to FixedStrike/Volatility
- **WHEN** `model.transform(XCoord.FixedStrike, YCoord.Volatility)` is called
- **THEN** the returned model SHALL evaluate in FixedStrike × Volatility space via `__call__`

#### Scenario: Access SABR params
- **WHEN** `model.params` is accessed
- **THEN** a dict `{"alpha": ..., "beta": ..., "rho": ..., "nu": ...}` SHALL be returned

### Requirement: SABRModel works with fit()
`SABRModel` SHALL be usable with the generic `fit()` function to calibrate to market data.

#### Scenario: Fit SABR to synthetic data
- **WHEN** `fit(sd, SABRModel)` is called with SmileData generated from known SABR parameters
- **THEN** `result.success` SHALL be `True` and `result.rmse` SHALL be small (< 1e-6 for noiseless data)
