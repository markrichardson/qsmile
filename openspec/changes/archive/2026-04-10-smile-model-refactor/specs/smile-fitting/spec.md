## MODIFIED Requirements

### Requirement: SmileResult contains fit diagnostics
The system SHALL return a `SmileResult` dataclass containing `params` (SmileModel instance with metadata and coordinate context), `residuals` (ndarray), `rmse` (float), and `success` (bool). The `params` field SHALL hold a fully coordinate-aware model instance.

#### Scenario: Access fitted parameters
- **WHEN** a user accesses `result.params` on a successful fit
- **THEN** the system SHALL return the fitted model instance with `metadata`, `current_x_coord`, and `current_y_coord` populated

#### Scenario: Fitted model is callable
- **WHEN** a user calls `result.params(x)` with x values
- **THEN** the system SHALL evaluate the fitted model at those points in the model's current coordinate system

#### Scenario: Access residuals
- **WHEN** a user accesses `result.residuals`
- **THEN** the system SHALL return a NumPy array of per-observation residuals (model minus observed values in native coordinates)

#### Scenario: Access RMSE
- **WHEN** a user accesses `result.rmse`
- **THEN** the system SHALL return the root mean square error of the fit

#### Scenario: Failed optimisation
- **WHEN** the optimiser fails to converge
- **THEN** `result.success` SHALL be `False` and `result.params` SHALL contain the best parameters found as a coordinate-aware model instance

## REMOVED Requirements

### Requirement: SmileResult provides evaluate method
**Reason**: Superseded by `result.params(x)` — the fitted model is now directly callable with coordinate-awareness.
**Migration**: Replace `result.evaluate(x)` with `result.params(x)`.

### Requirement: fit_svi calibrates SVI to option chain data
**Reason**: The generic `fit()` function handles all model types uniformly. Model-specific convenience wrappers are unnecessary.
**Migration**: Replace `fit_svi(chain)` with `fit(chain, SVIModel)`.

### Requirement: fit_svi enforces parameter bounds
**Reason**: Removed along with `fit_svi`. Bounds enforcement is handled by the generic `fit()` via each model's `bounds` class variable.
**Migration**: Use `fit(chain, SVIModel)` — bounds enforcement is automatic.

## MODIFIED Requirements

### Requirement: fit() populates model with metadata and coordinates
The `fit()` function SHALL construct the fitted model instance with the `SmileMetadata` from the input `SmileData` and set `current_x_coord`/`current_y_coord` to the model's native coordinates.

#### Scenario: Fitted model carries metadata
- **WHEN** `fit(sd, SVIModel)` completes successfully
- **THEN** `result.params.metadata` SHALL be populated from the input `SmileData`'s metadata

#### Scenario: Fitted model in native coords
- **WHEN** `fit(sd, SVIModel)` completes
- **THEN** `result.params.current_x_coord` SHALL equal `SVIModel.native_x_coord`
- **AND** `result.params.current_y_coord` SHALL equal `SVIModel.native_y_coord`

#### Scenario: Fitted model can be transformed
- **WHEN** `result.params.transform(XCoord.FixedStrike, YCoord.Volatility)` is called after fitting
- **THEN** the returned model SHALL evaluate correctly in the new coordinate system
