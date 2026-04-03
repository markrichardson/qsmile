## ADDED Requirements

### Requirement: Generic fit function calibrates any SmileModel to SmileData
The system SHALL provide a `fit(chain: SmileData, model: SmileModel, initial_params: SmileModel | None = None) -> SmileResult` function that fits any model conforming to the `SmileModel` protocol. The function SHALL transform the input `SmileData` to the model's native coordinates before fitting.

#### Scenario: Fit SVI via generic fit
- **WHEN** `fit` is called with a `SmileData` and an SVI model instance
- **THEN** the returned `SmileResult` SHALL contain fitted SVI parameters and `success=True`

#### Scenario: Fit with data in non-native coordinates
- **WHEN** `fit` is called with a `SmileData` in `(FixedStrike, Volatility)` and an SVI model
- **THEN** the system SHALL internally transform to `(LogMoneynessStrike, TotalVariance)` and fit successfully

#### Scenario: Fit with custom initial params
- **WHEN** `fit` is called with `initial_params` set to a model instance
- **THEN** the optimiser SHALL use `initial_params.to_array()` as the starting point

#### Scenario: Fit without initial params
- **WHEN** `fit` is called without `initial_params`
- **THEN** the system SHALL call `model.initial_guess(x, y)` to compute a heuristic starting point

### Requirement: Generic fit uses model bounds
The `fit` function SHALL pass `model.bounds` to the optimiser as box constraints.

#### Scenario: Fitted parameters within model bounds
- **WHEN** `fit` completes successfully
- **THEN** all fitted parameters SHALL satisfy the model's declared bounds

### Requirement: Generic fit returns model-agnostic SmileResult
The `fit` function SHALL return a `SmileResult` whose `params` field is a `SmileModel` instance reconstructed via `model.from_array()`.

#### Scenario: Result params match model type
- **WHEN** `fit` is called with an SVI model
- **THEN** `result.params` SHALL be an instance that satisfies the `SmileModel` protocol and represents fitted SVI parameters
