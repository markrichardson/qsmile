## MODIFIED Requirements

### Requirement: SmileResult contains fit diagnostics
The system SHALL return a `SmileResult` dataclass containing `params` (SmileModel instance), `residuals` (ndarray), `rmse` (float), and `success` (bool). The `params` field SHALL hold the fitted model instance rather than being restricted to `SVIParams`.

#### Scenario: Access fitted parameters
- **WHEN** a user accesses `result.params` on a successful fit
- **THEN** the system SHALL return the fitted model instance (e.g. an SVI model with fitted parameters)

#### Scenario: Access residuals
- **WHEN** a user accesses `result.residuals`
- **THEN** the system SHALL return a NumPy array of per-observation residuals (model minus observed values in native coordinates)

#### Scenario: Access RMSE
- **WHEN** a user accesses `result.rmse`
- **THEN** the system SHALL return the root mean square error of the fit

#### Scenario: Failed optimisation
- **WHEN** the optimiser fails to converge
- **THEN** `result.success` SHALL be `False` and `result.params` SHALL contain the best parameters found

### Requirement: SmileResult provides evaluate method
The system SHALL provide an `evaluate(x)` method on `SmileResult` that computes the model output at arbitrary x values in the model's native coordinate system using the fitted parameters.

#### Scenario: Evaluate at new x values
- **WHEN** `result.evaluate(x)` is called with a NumPy array of x values
- **THEN** the system SHALL return the model output at those points using the fitted parameters

### Requirement: fit_svi calibrates SVI to option chain data
The system SHALL provide a `fit_svi(chain: SmileData, initial_params: SVIParams | None = None) -> SmileResult` convenience function that delegates to the generic `fit()` with an SVI model. The function SHALL be functionally equivalent to the previous implementation.

#### Scenario: Fit to synthetic SVI data
- **WHEN** `fit_svi` is called with a `SmileData` whose implied vols were generated from known SVI parameters
- **THEN** the returned `SmileResult` SHALL contain parameters that recover the original parameters within a tight tolerance

#### Scenario: SmileData in any coordinate system accepted
- **WHEN** `fit_svi` is called with a `SmileData` in `(FixedStrike, Volatility)` coordinates
- **THEN** the system SHALL internally transform to `(LogMoneynessStrike, TotalVariance)` and fit successfully

#### Scenario: fit_svi accepts optional SVIParams initial guess
- **WHEN** `fit_svi` is called with a user-provided `initial_params: SVIParams`
- **THEN** the optimiser SHALL use those values as the starting point

### Requirement: fit_svi enforces parameter bounds
The system SHALL apply box constraints during optimisation: $b \geq 0$, $-1 < \rho < 1$, $\sigma > 0$.

#### Scenario: Fitted parameters within bounds
- **WHEN** `fit_svi` completes successfully
- **THEN** all returned parameters SHALL satisfy the SVI parameter constraints
