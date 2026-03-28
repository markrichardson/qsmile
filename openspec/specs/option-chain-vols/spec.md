## ADDED Requirements

### Requirement: OptionChainVols stores bid/ask implied volatilities
The system SHALL provide an `OptionChainVols` dataclass that holds strikes, bid and ask implied volatilities, forward price, discount factor, and time to expiry for a single-expiry option chain. All array fields SHALL be NumPy float64 arrays.

#### Scenario: Construct from arrays
- **WHEN** a user creates an `OptionChainVols` with strikes, vol_bid, vol_ask, forward, discount_factor, and expiry
- **THEN** all fields SHALL be stored and accessible as attributes

#### Scenario: Construct from lists
- **WHEN** Python lists are passed for array fields
- **THEN** the system SHALL convert them to NumPy float64 arrays automatically

### Requirement: OptionChainVols validates inputs
The system SHALL validate volatility data on construction.

#### Scenario: Mismatched array lengths
- **WHEN** vol_bid or vol_ask has a different length from strikes
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Negative implied volatilities
- **WHEN** any bid or ask implied volatility is negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Bid exceeds ask
- **WHEN** any vol_bid exceeds the corresponding vol_ask
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive forward
- **WHEN** the forward is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive discount factor
- **WHEN** the discount_factor is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive expiry
- **WHEN** the expiry is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Fewer than three strikes
- **WHEN** fewer than 3 strikes are provided
- **THEN** the system SHALL raise a `ValueError`

### Requirement: OptionChainVols provides mid implied volatilities
The system SHALL provide a `vol_mid` property that returns the midpoint of bid and ask implied volatilities.

#### Scenario: Mid vol computation
- **WHEN** `vol_mid` is accessed
- **THEN** the system SHALL return `(vol_bid + vol_ask) / 2` as a NumPy array

### Requirement: OptionChainVols computes log-moneyness
The system SHALL provide a `log_moneyness` property returning $k = \ln(K / F)$ for each strike.

#### Scenario: Log-moneyness access
- **WHEN** `log_moneyness` is accessed
- **THEN** the system SHALL return a NumPy array of $\ln(\text{strike} / \text{forward})$

### Requirement: OptionChainVols computes ATM implied volatility
The system SHALL provide a `sigma_atm` property that returns the mid implied volatility at the strike closest to the forward.

#### Scenario: ATM vol selection
- **WHEN** `sigma_atm` is accessed
- **THEN** the system SHALL return the mid implied vol at the strike with smallest $|K - F|$

### Requirement: OptionChainVols converts to UnitisedSpaceVols
The system SHALL provide a `to_unitised()` method that converts the vol chain to `UnitisedSpaceVols` using the normalised coordinates $\tilde{k} = \log(K/F) / (\sigma_{\text{ATM}} \sqrt{t})$ and $v = \sigma_k^2 \, t$.

#### Scenario: Unitised conversion
- **WHEN** `to_unitised()` is called
- **THEN** the system SHALL return a `UnitisedSpaceVols` with correctly normalised coordinates for both bid and ask

### Requirement: OptionChainVols converts to prices
The system SHALL provide a `to_prices()` method that converts vol chain back to an `OptionChainPrices` using Black76 pricing.

#### Scenario: Vol to price round-trip
- **WHEN** an `OptionChainPrices` is converted to vols via `to_vols()` and back via `to_prices()`
- **THEN** the recovered prices SHALL match the originals within floating-point tolerance

### Requirement: OptionChainVols converts to OptionChain
The system SHALL provide a `to_option_chain()` method that produces the existing `OptionChain` dataclass using mid implied volatilities, enabling use with the existing `fit_svi` pipeline.

#### Scenario: Conversion to legacy OptionChain
- **WHEN** `to_option_chain()` is called
- **THEN** the system SHALL return an `OptionChain` with mid vols, forward, and expiry
