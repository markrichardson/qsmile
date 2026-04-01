## Requirements

### Requirement: fit_svi calibrates SVI to option chain data
The system SHALL provide a `fit_svi(chain: SmileData) -> SmileResult` function that fits SVI raw parameters to the market data in the SmileData by minimising the sum of squared residuals between model and observed total variance. The input SmileData SHALL be internally transformed to `(LogMoneynessStrike, TotalVariance)` coordinates before fitting.

#### Scenario: Fit to synthetic SVI data
- **WHEN** `fit_svi` is called with a `SmileData` whose implied vols were generated from known SVI parameters
- **THEN** the returned `SmileResult` SHALL contain `SVIParams` that recover the original parameters within a tight tolerance

#### Scenario: Fit to noisy market-like data
- **WHEN** `fit_svi` is called with realistic market data (e.g. a smile with skew)
- **THEN** the returned `SmileResult` SHALL have `success=True` and an RMSE below a reasonable threshold

#### Scenario: SmileData in any coordinate system accepted
- **WHEN** `fit_svi` is called with a `SmileData` in `(FixedStrike, Volatility)` coordinates
- **THEN** the system SHALL internally transform to `(LogMoneynessStrike, TotalVariance)` and fit successfully

#### Scenario: SmileData from prices accepted
- **WHEN** `fit_svi` is called with a `SmileData` in `(FixedStrike, Price)` coordinates
- **THEN** the system SHALL internally transform to `(LogMoneynessStrike, TotalVariance)` and fit successfully

### Requirement: fit_svi accepts optional initial guess
The system SHALL allow the user to pass an optional `initial_params: SVIParams` argument to `fit_svi` to seed the optimiser.

#### Scenario: Custom initial guess
- **WHEN** `fit_svi` is called with a user-provided `initial_params`
- **THEN** the optimiser SHALL use those values as the starting point instead of the heuristic default

#### Scenario: No initial guess provided
- **WHEN** `fit_svi` is called without `initial_params`
- **THEN** the system SHALL compute an automatic heuristic initial guess from the option chain data

### Requirement: SmileResult contains fit diagnostics
The system SHALL return a `SmileResult` dataclass containing `params` (SVIParams), `residuals` (ndarray), `rmse` (float), and `success` (bool).

#### Scenario: Access fitted parameters
- **WHEN** a user accesses `result.params` on a successful fit
- **THEN** the system SHALL return the fitted `SVIParams`

#### Scenario: Access residuals
- **WHEN** a user accesses `result.residuals`
- **THEN** the system SHALL return a NumPy array of per-observation residuals (model minus observed total variance)

#### Scenario: Access RMSE
- **WHEN** a user accesses `result.rmse`
- **THEN** the system SHALL return the root mean square error of the fit

#### Scenario: Failed optimisation
- **WHEN** the optimiser fails to converge
- **THEN** `result.success` SHALL be `False` and `result.params` SHALL contain the best parameters found

### Requirement: SmileResult provides evaluate method
The system SHALL provide an `evaluate(k)` method on `SmileResult` that computes SVI total variance at arbitrary log-moneyness values using the fitted parameters.

#### Scenario: Evaluate at new strikes
- **WHEN** `result.evaluate(k)` is called with a NumPy array of log-moneyness values
- **THEN** the system SHALL return the SVI total variance at those points using the fitted parameters

### Requirement: fit_svi enforces parameter bounds
The system SHALL apply box constraints during optimisation: $b \geq 0$, $-1 < \rho < 1$, $\sigma > 0$.

#### Scenario: Fitted parameters within bounds
- **WHEN** `fit_svi` completes successfully
- **THEN** all returned parameters SHALL satisfy the SVI parameter constraints
