## ADDED Requirements

### Requirement: VolData provides evaluate for mid-curve interpolation
`VolData` SHALL provide an `evaluate(x)` method that returns interpolated mid-smile values (`y_mid`) at arbitrary x positions in the current coordinate system. The interpolation SHALL use cubic spline interpolation on the mid values in current coordinates.

#### Scenario: Evaluate at data points returns mid values
- **WHEN** `evaluate(x)` is called with x values that exactly match existing data points
- **THEN** the returned values SHALL equal `y_mid` at those points within floating-point tolerance

#### Scenario: Evaluate between data points interpolates
- **WHEN** `evaluate(x)` is called with x values between existing data points
- **THEN** the returned values SHALL be cubic spline interpolated mid values

#### Scenario: Evaluate outside data domain returns NaN
- **WHEN** `evaluate(x)` is called with x values outside the range of the data
- **THEN** the returned values SHALL be `NaN`

#### Scenario: Evaluate respects current coordinate system
- **WHEN** `data.transform(XCoord.LogMoneynessStrike, YCoord.Volatility).evaluate(log_k)` is called
- **THEN** the input `log_k` SHALL be interpreted as log-moneyness values
- **AND** the output SHALL be volatility values

#### Scenario: Evaluate accepts array-like input
- **WHEN** `evaluate(x)` is called with a list, tuple, or NumPy array
- **THEN** the result SHALL be an `NDArray[np.float64]`
