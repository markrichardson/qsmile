## MODIFIED Requirements

### Requirement: SmileResult contains fit diagnostics
The system SHALL return a `SmileResult` dataclass containing `params` (SmileModel instance with metadata and coordinate context), `residuals` (ndarray), `rmse` (float), and `success` (bool). The `params` field SHALL hold a fully coordinate-aware model instance. The fitted model is NOT callable — use `result.params.evaluate(x)`.

#### Scenario: Access fitted parameters
- **WHEN** a user accesses `result.params` on a successful fit
- **THEN** the system SHALL return the fitted model instance with `metadata`, `current_x_coord`, and `current_y_coord` populated

#### Scenario: Evaluate fitted model
- **WHEN** a user calls `result.params.evaluate(x)` with x values
- **THEN** the system SHALL evaluate the fitted model at those points in the model's current coordinate system

#### Scenario: Transform then evaluate fitted model
- **WHEN** a user calls `result.params.transform(XCoord.FixedStrike, YCoord.Volatility).evaluate(strikes)`
- **THEN** the system SHALL evaluate the fitted model in the target coordinate system

#### Scenario: Access residuals
- **WHEN** a user accesses `result.residuals`
- **THEN** the system SHALL return a NumPy array of per-observation residuals (model minus observed values in native coordinates)

#### Scenario: Access RMSE
- **WHEN** a user accesses `result.rmse`
- **THEN** the system SHALL return the root mean square error of the fit

#### Scenario: Failed optimisation
- **WHEN** the optimiser fails to converge
- **THEN** `result.success` SHALL be `False` and `result.params` SHALL contain the best parameters found as a coordinate-aware model instance

### Requirement: fit() populates model with metadata and coordinates
The `fit()` function SHALL construct the fitted model instance with the `SmileMetadata` from the input `SmileData` and set `current_x_coord`/`current_y_coord` to the model's native coordinates. Type hints SHALL use `SmileModel` ABC directly (no separate Protocol).

#### Scenario: Fitted model carries metadata
- **WHEN** `fit(sd, SVIModel)` completes successfully
- **THEN** `result.params.metadata` SHALL be populated from the input `SmileData`'s metadata

#### Scenario: Fitted model in native coords
- **WHEN** `fit(sd, SVIModel)` completes
- **THEN** `result.params.current_x_coord` SHALL equal `SVIModel.native_x_coord`
- **AND** `result.params.current_y_coord` SHALL equal `SVIModel.native_y_coord`

#### Scenario: Fitted model can be transformed and evaluated
- **WHEN** `result.params.transform(XCoord.FixedStrike, YCoord.Volatility).evaluate(strikes)` is called after fitting
- **THEN** the returned values SHALL be implied volatilities at the given strikes

### Requirement: fit() internal residuals use _evaluate
The `fit()` function's internal `_residuals()` helper SHALL call `model._evaluate(x)` (not `evaluate(x)`) since residuals are always computed in native coordinates.

#### Scenario: Residuals computed in native coords
- **WHEN** `fit()` is running the optimiser
- **THEN** residuals SHALL be computed by calling `_evaluate()` on candidate models in native coordinates
