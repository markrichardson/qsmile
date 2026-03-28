## ADDED Requirements

### Requirement: OptionChainPrices stores bid/ask option prices
The system SHALL provide an `OptionChainPrices` dataclass that holds strikes, bid and ask prices for calls and puts, and the time to expiry for a single-expiry option chain. Strikes SHALL be stored as a NumPy array. Bid and ask prices for calls and puts SHALL each be stored as NumPy arrays of the same length as strikes.

#### Scenario: Construct from arrays
- **WHEN** a user creates an `OptionChainPrices` with arrays of strikes, call_bid, call_ask, put_bid, put_ask, and expiry
- **THEN** all fields SHALL be stored and accessible as attributes

#### Scenario: Construct from lists
- **WHEN** a user passes Python lists for price arrays
- **THEN** the system SHALL convert them to NumPy float64 arrays automatically

### Requirement: OptionChainPrices validates inputs
The system SHALL validate price data on construction.

#### Scenario: Mismatched array lengths
- **WHEN** any price array has a different length from strikes
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive strikes
- **WHEN** any strike is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Negative prices
- **WHEN** any bid or ask price is negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Bid exceeds ask
- **WHEN** any bid price exceeds the corresponding ask price
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive expiry
- **WHEN** the expiry is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Fewer than three strikes
- **WHEN** fewer than 3 strikes are provided
- **THEN** the system SHALL raise a `ValueError`

### Requirement: OptionChainPrices accepts optional forward and discount factor
The system SHALL accept optional `forward` and `discount_factor` parameters. When provided, they SHALL be used directly. When omitted, they SHALL be calibrated from the price data.

#### Scenario: User provides forward and discount factor
- **WHEN** `forward` and `discount_factor` are both supplied
- **THEN** the system SHALL use those values without running calibration

#### Scenario: Neither forward nor discount factor provided
- **WHEN** both `forward` and `discount_factor` are omitted
- **THEN** the system SHALL calibrate them from put-call parity

### Requirement: Forward and discount factor calibration via put-call parity
The system SHALL calibrate forward and discount factor by fitting the put-call parity relation $C_{\text{mid}} - P_{\text{mid}} = D(F - K)$ using weighted least squares with a delta-blend weighting scheme. The optimisation SHALL use `cvxpy` with constraints $F > 0$ and $0 < D \leq 1$.

#### Scenario: Calibrated forward accuracy
- **WHEN** prices are generated from a known forward and discount factor
- **THEN** the calibrated forward SHALL match the true forward within a reasonable tolerance

#### Scenario: Calibrated discount factor accuracy
- **WHEN** prices are generated from a known discount factor
- **THEN** the calibrated discount factor SHALL match the true value within a reasonable tolerance

#### Scenario: Delta-blend weighting tilts towards ATM
- **WHEN** calibration is run
- **THEN** strikes near ATM SHALL receive higher weight than deep OTM/ITM strikes

#### Scenario: Calibrated values satisfy constraints
- **WHEN** calibration completes
- **THEN** the forward SHALL be positive and the discount factor SHALL be in (0, 1]

### Requirement: OptionChainPrices provides mid prices
The system SHALL provide properties `call_mid` and `put_mid` that return the midpoint of bid and ask for calls and puts respectively.

#### Scenario: Mid price computation
- **WHEN** `call_mid` or `put_mid` is accessed
- **THEN** the system SHALL return `(bid + ask) / 2` as a NumPy array

### Requirement: OptionChainPrices converts to OptionChainVols
The system SHALL provide a `to_vols()` method that converts the price chain to an `OptionChainVols` by inverting bid and ask prices through Black76.

#### Scenario: Price to vol conversion
- **WHEN** `to_vols()` is called on a valid `OptionChainPrices`
- **THEN** the system SHALL return an `OptionChainVols` with bid and ask implied volatilities for each strike
