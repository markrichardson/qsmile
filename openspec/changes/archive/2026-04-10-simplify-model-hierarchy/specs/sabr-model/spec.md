## MODIFIED Requirements

### Requirement: SABRModel represents SABR parameters
The system SHALL provide a `SABRModel` dataclass inheriting from `SmileModel` (formerly `AbstractSmileModel`) with fitted fields `alpha`, `beta`, `rho`, `nu`. Context is provided via `metadata: SmileMetadata` inherited from `SmileModel`.

#### Scenario: Create SABRModel with metadata
- **WHEN** a user constructs `SABRModel(alpha=0.2, beta=0.5, rho=-0.3, nu=0.4, metadata=meta)` where `meta` contains expiry and forward
- **THEN** the four fitted fields and metadata are stored and accessible as attributes
- **AND** `metadata.texpiry` provides the time to expiry
- **AND** `metadata.forward` provides the forward price

#### Scenario: SABRModel is a SmileModel subclass
- **WHEN** a `SABRModel` instance is checked with `isinstance(m, SmileModel)`
- **THEN** the check SHALL return `True`

### Requirement: SABRModel implements _evaluate for native computation
`SABRModel` SHALL implement `_evaluate(x)` using Hagan et al. (2002) lognormal implied volatility approximation, where `x` is log-moneyness and the result is implied volatility. The method SHALL read `expiry` and `forward` from `self.metadata`.

#### Scenario: _evaluate at ATM
- **WHEN** `model._evaluate(0.0)` is called (ATM, log-moneyness = 0)
- **THEN** the result SHALL be a finite positive implied volatility

#### Scenario: _evaluate at array of strikes
- **WHEN** `model._evaluate(k)` is called with a NumPy array of log-moneyness values
- **THEN** the result SHALL be a NumPy array of the same length containing positive implied volatilities

### Requirement: SABRModel supports transform and evaluate
`SABRModel` SHALL inherit `transform()`, `evaluate()`, `plot()`, and `params` from `SmileModel`. The `evaluate()` method SHALL be coordinate-aware. `SABRModel` SHALL NOT have a `__call__` method.

#### Scenario: Transform SABR to FixedStrike/Volatility then evaluate
- **WHEN** `model.transform(XCoord.FixedStrike, YCoord.Volatility).evaluate(strikes)` is called
- **THEN** the result SHALL be implied volatilities at the given strikes

#### Scenario: Access SABR params
- **WHEN** `model.params` is accessed
- **THEN** a dict `{"alpha": ..., "beta": ..., "rho": ..., "nu": ...}` SHALL be returned

## REMOVED Requirements

### Requirement: SABRModel supports transform and __call__
**Reason**: `__call__` is removed. Replaced by coordinate-aware `evaluate()`.
**Migration**: Replace `model(x)` with `model.evaluate(x)`. Replace `model.transform(x, y)(k)` with `model.transform(x, y).evaluate(k)`.
