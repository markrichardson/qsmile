## MODIFIED Requirements

### Requirement: SVIModel represents raw SVI parameters
The system SHALL provide an `SVIModel` dataclass inheriting from `SmileModel` (formerly `AbstractSmileModel`) with fitted fields `a`, `b`, `rho`, `m`, and `sigma` representing the five raw SVI parameters. `SVIModel` SHALL carry `metadata: SmileMetadata`, `current_x_coord`, and `current_y_coord` inherited from `SmileModel`.

#### Scenario: Create SVIModel with metadata
- **WHEN** a user constructs `SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2, metadata=meta)`
- **THEN** all five parameters and metadata are stored and accessible as attributes
- **AND** `current_x_coord` SHALL default to `XCoord.LogMoneynessStrike`
- **AND** `current_y_coord` SHALL default to `YCoord.TotalVariance`

#### Scenario: SVIModel is a SmileModel subclass
- **WHEN** an `SVIModel` instance is checked with `isinstance(m, SmileModel)`
- **THEN** the check SHALL return `True`

### Requirement: SVIModel provides parameter serialisation
`SVIModel` SHALL inherit `to_array()` and `from_array()` from `SmileModel`. The serialisation SHALL produce `[a, b, rho, m, sigma]` based on `param_names`. `from_array` SHALL accept metadata.

#### Scenario: Round-trip serialisation
- **WHEN** `SVIModel.from_array(model.to_array(), metadata=model.metadata)` is called
- **THEN** the resulting `SVIModel` SHALL have the same field values

#### Scenario: from_array returns SVIModel instance
- **WHEN** `SVIModel.from_array(arr, metadata=meta)` is called
- **THEN** the result SHALL be an instance of `SVIModel` with the provided metadata

### Requirement: SVIModel implements _evaluate for native computation
`SVIModel` SHALL implement `_evaluate(x)` computing total variance via the SVI formula `w(k) = a + b * (rho * (k - m) + sqrt((k - m)^2 + sigma^2))` where x is log-moneyness in native coordinates.

#### Scenario: _evaluate at scalar
- **WHEN** `model._evaluate(0.0)` is called
- **THEN** the result SHALL be a float equal to the SVI formula at k=0

#### Scenario: _evaluate at array
- **WHEN** `model._evaluate(k)` is called with a NumPy array
- **THEN** the result SHALL be a NumPy array of the same length

### Requirement: SVIModel supports transform and evaluate
`SVIModel` SHALL inherit `transform()`, `evaluate()`, `plot()`, and `params` from `SmileModel`. The `evaluate()` method SHALL be coordinate-aware. `SVIModel` SHALL NOT have a `__call__` method.

#### Scenario: Transform SVI to FixedStrike/Volatility then evaluate
- **WHEN** `model.transform(XCoord.FixedStrike, YCoord.Volatility).evaluate(strikes)` is called
- **THEN** the result SHALL be implied volatilities at the given strikes

#### Scenario: Plot SVI model
- **WHEN** `model.plot()` is called
- **THEN** a matplotlib Figure SHALL be returned

#### Scenario: Access SVI params
- **WHEN** `model.params` is accessed
- **THEN** a dict `{"a": ..., "b": ..., "rho": ..., "m": ..., "sigma": ...}` SHALL be returned

## REMOVED Requirements

### Requirement: SVIModel supports transform and __call__
**Reason**: `__call__` is removed. Replaced by coordinate-aware `evaluate()`.
**Migration**: Replace `model(x)` with `model.evaluate(x)`. Replace `model.transform(x, y)(k)` with `model.transform(x, y).evaluate(k)`.

### Requirement: SVIModel provides implied_vol
**Reason**: `implied_vol(k, expiry)` was an SVI-specific convenience method that broke symmetry with other models. The same result is achieved via the coordinate transform system.
**Migration**: Replace `model.implied_vol(k, t)` with `model.transform(XCoord.LogMoneynessStrike, YCoord.Volatility).evaluate(k)`.
