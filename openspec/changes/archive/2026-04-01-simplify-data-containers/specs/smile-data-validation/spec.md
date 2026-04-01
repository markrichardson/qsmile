## ADDED Requirements

### Requirement: SmileData validates minimum data points
The system SHALL require at least 3 data points in `x`, `y_bid`, and `y_ask` arrays. Construction with fewer than 3 points SHALL raise a `ValueError`.

#### Scenario: Fewer than 3 points rejected
- **WHEN** a `SmileData` is constructed with arrays of length 2
- **THEN** the system SHALL raise a `ValueError` with a message indicating at least 3 points are required

#### Scenario: Exactly 3 points accepted
- **WHEN** a `SmileData` is constructed with arrays of length 3
- **THEN** the construction SHALL succeed

### Requirement: SmileData validates bid-ask ordering
The system SHALL require `y_bid[i] <= y_ask[i]` for all elements. Construction with any `y_bid > y_ask` SHALL raise a `ValueError`.

#### Scenario: Bid exceeds ask rejected
- **WHEN** a `SmileData` is constructed with any `y_bid[i] > y_ask[i]`
- **THEN** the system SHALL raise a `ValueError`

### Requirement: SmileData validates FixedStrike positivity
When `x_coord` is `FixedStrike`, the system SHALL require all `x` values to be positive. Construction with non-positive strikes SHALL raise a `ValueError`.

#### Scenario: Non-positive fixed strike rejected
- **WHEN** a `SmileData` is constructed with `x_coord=FixedStrike` and any `x[i] <= 0`
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Positive fixed strikes accepted
- **WHEN** a `SmileData` is constructed with `x_coord=FixedStrike` and all `x[i] > 0`
- **THEN** the construction SHALL succeed

### Requirement: SmileData validates MoneynessStrike positivity
When `x_coord` is `MoneynessStrike`, the system SHALL require all `x` values to be positive. Construction with non-positive moneyness SHALL raise a `ValueError`.

#### Scenario: Non-positive moneyness strike rejected
- **WHEN** a `SmileData` is constructed with `x_coord=MoneynessStrike` and any `x[i] <= 0`
- **THEN** the system SHALL raise a `ValueError`

### Requirement: SmileData validates Volatility non-negativity
When `y_coord` is `Volatility`, the system SHALL require all `y_bid` and `y_ask` values to be non-negative. Construction with negative volatilities SHALL raise a `ValueError`.

#### Scenario: Negative volatility rejected
- **WHEN** a `SmileData` is constructed with `y_coord=Volatility` and any `y_bid[i] < 0` or `y_ask[i] < 0`
- **THEN** the system SHALL raise a `ValueError`

### Requirement: SmileData validates Variance non-negativity
When `y_coord` is `Variance` or `TotalVariance`, the system SHALL require all `y_bid` and `y_ask` values to be non-negative. Construction with negative variances SHALL raise a `ValueError`.

#### Scenario: Negative variance rejected
- **WHEN** a `SmileData` is constructed with `y_coord=Variance` and any `y_bid[i] < 0`
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Negative total variance rejected
- **WHEN** a `SmileData` is constructed with `y_coord=TotalVariance` and any `y_ask[i] < 0`
- **THEN** the system SHALL raise a `ValueError`
