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

### Requirement: OptionChain accepts optional volume data
The system SHALL accept an optional `volume` parameter of type `NDArray[np.float64] | None` (default `None`) representing per-strike traded volume.

#### Scenario: Construct OptionChain with volume
- **WHEN** a user creates an `OptionChain` with a `volume` array of the same length as strikes
- **THEN** the `volume` field SHALL be stored as a NumPy float64 array and accessible as an attribute

#### Scenario: Construct OptionChain without volume
- **WHEN** a user creates an `OptionChain` without providing `volume`
- **THEN** the `volume` field SHALL be `None`

#### Scenario: Volume array length mismatch rejected
- **WHEN** `volume` is provided with a different length than strikes
- **THEN** the system SHALL raise a `ValueError` with a message indicating the length mismatch

#### Scenario: Negative volume rejected
- **WHEN** any value in `volume` is negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: OptionChain accepts optional open interest data
The system SHALL accept an optional `open_interest` parameter of type `NDArray[np.float64] | None` (default `None`) representing per-strike open interest.

#### Scenario: Construct OptionChain with open interest
- **WHEN** a user creates an `OptionChain` with an `open_interest` array of the same length as strikes
- **THEN** the `open_interest` field SHALL be stored as a NumPy float64 array and accessible as an attribute

#### Scenario: Construct OptionChain without open interest
- **WHEN** a user creates an `OptionChain` without providing `open_interest`
- **THEN** the `open_interest` field SHALL be `None`

#### Scenario: Open interest array length mismatch rejected
- **WHEN** `open_interest` is provided with a different length than strikes
- **THEN** the system SHALL raise a `ValueError` with a message indicating the length mismatch

#### Scenario: Negative open interest rejected
- **WHEN** any value in `open_interest` is negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: OptionChain filter preserves volume and open interest
The `filter()` method SHALL propagate `volume` and `open_interest` arrays to the returned `OptionChain`, subsetting them with the same mask used to filter strikes. If the source arrays are `None`, the returned chain's arrays SHALL also be `None`.

#### Scenario: Denoise subsets volume and open interest
- **WHEN** `filter()` is called on an `OptionChain` with `volume` and `open_interest`
- **THEN** the returned chain's `volume` and `open_interest` SHALL contain only the entries corresponding to the surviving strikes

#### Scenario: Denoise with None volume and open interest
- **WHEN** `filter()` is called on an `OptionChain` where `volume` and `open_interest` are `None`
- **THEN** the returned chain's `volume` and `open_interest` SHALL be `None`
