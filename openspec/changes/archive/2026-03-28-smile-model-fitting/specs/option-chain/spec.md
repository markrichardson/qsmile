## ADDED Requirements

### Requirement: OptionChain stores market data
The system SHALL provide an `OptionChain` dataclass that holds strikes, implied volatilities, forward price, and expiry (time to expiration in years) as its core fields. Strikes and implied volatilities SHALL be stored as NumPy arrays.

#### Scenario: Construct OptionChain from arrays
- **WHEN** a user creates an `OptionChain` with arrays of strikes, implied volatilities, a forward price, and expiry
- **THEN** the `OptionChain` stores all fields and they are accessible as attributes

#### Scenario: Construct OptionChain from lists
- **WHEN** a user passes Python lists for strikes and implied volatilities
- **THEN** the `OptionChain` SHALL convert them to NumPy arrays automatically

### Requirement: OptionChain validates inputs
The system SHALL validate option chain data on construction, rejecting invalid inputs with clear error messages.

#### Scenario: Mismatched array lengths
- **WHEN** strikes and implied volatilities have different lengths
- **THEN** the system SHALL raise a `ValueError` with a message indicating the length mismatch

#### Scenario: Non-positive forward price
- **WHEN** the forward price is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive expiry
- **WHEN** the expiry is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Negative implied volatility
- **WHEN** any implied volatility value is negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive strike
- **WHEN** any strike value is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Fewer than three data points
- **WHEN** the user supplies fewer than 3 strike/IV pairs
- **THEN** the system SHALL raise a `ValueError` (SVI has 5 parameters; minimum 3 points needed for any meaningful fit)

### Requirement: OptionChain computes log-moneyness
The system SHALL provide a `log_moneyness` property that returns $k = \ln(K / F)$ for each strike.

#### Scenario: Log-moneyness computation
- **WHEN** the `log_moneyness` property is accessed on a valid `OptionChain`
- **THEN** the system SHALL return a NumPy array of $\ln(\text{strike} / \text{forward})$ values

### Requirement: OptionChain computes total variance
The system SHALL provide a `total_variance` property that returns $w = \sigma_{IV}^2 \cdot T$ for each observation.

#### Scenario: Total variance computation
- **WHEN** the `total_variance` property is accessed
- **THEN** the system SHALL return a NumPy array of implied variance times expiry
