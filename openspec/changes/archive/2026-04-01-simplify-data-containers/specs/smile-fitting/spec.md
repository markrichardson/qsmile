## MODIFIED Requirements

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
