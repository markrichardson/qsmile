## ADDED Requirements

### Requirement: Black76 call price
The system SHALL provide a function `black76_call(forward, strike, discount_factor, vol, expiry)` that returns the Black76 call option price: $C = D \bigl[F\,\Phi(d_1) - K\,\Phi(d_2)\bigr]$ where $d_1 = \frac{\ln(F/K) + \frac{1}{2}\sigma^2 T}{\sigma\sqrt{T}}$, $d_2 = d_1 - \sigma\sqrt{T}$, $\Phi$ is the standard normal CDF, $D$ is the discount factor, $F$ is the forward, $K$ is the strike, $\sigma$ is the volatility, and $T$ is the time to expiry.

#### Scenario: ATM call price
- **WHEN** `black76_call` is called with `forward=100`, `strike=100`, `discount_factor=1.0`, `vol=0.2`, `expiry=1.0`
- **THEN** the returned price SHALL match the known analytical ATM Black76 result within floating-point tolerance

#### Scenario: Deep ITM call
- **WHEN** `black76_call` is called with `strike` much less than `forward`
- **THEN** the returned price SHALL approach `discount_factor * (forward - strike)`

#### Scenario: Deep OTM call
- **WHEN** `black76_call` is called with `strike` much greater than `forward`
- **THEN** the returned price SHALL approach zero

#### Scenario: Zero vol call
- **WHEN** `vol=0.0` and `forward > strike`
- **THEN** the returned price SHALL equal `discount_factor * (forward - strike)`

#### Scenario: Vectorised call pricing
- **WHEN** `black76_call` is called with NumPy arrays for `strike` and/or `vol`
- **THEN** the function SHALL return a NumPy array of prices with matching shape

### Requirement: Black76 put price
The system SHALL provide a function `black76_put(forward, strike, discount_factor, vol, expiry)` that returns the Black76 put option price: $P = D \bigl[K\,\Phi(-d_2) - F\,\Phi(-d_1)\bigr]$.

#### Scenario: ATM put price
- **WHEN** `black76_put` is called with `forward=100`, `strike=100`, `discount_factor=1.0`, `vol=0.2`, `expiry=1.0`
- **THEN** the returned price SHALL match the known analytical ATM Black76 result

#### Scenario: Put-call parity
- **WHEN** both `black76_call` and `black76_put` are called with the same inputs
- **THEN** the prices SHALL satisfy $C - P = D(F - K)$ within floating-point tolerance

#### Scenario: Vectorised put pricing
- **WHEN** `black76_put` is called with NumPy arrays for `strike`
- **THEN** the function SHALL return a NumPy array of prices with matching shape

### Requirement: Black76 input validation
The system SHALL validate inputs to all Black76 functions.

#### Scenario: Non-positive forward
- **WHEN** `forward` is zero or negative
- **THEN** the function SHALL raise a `ValueError`

#### Scenario: Non-positive strike
- **WHEN** any `strike` is zero or negative
- **THEN** the function SHALL raise a `ValueError`

#### Scenario: Non-positive expiry
- **WHEN** `expiry` is zero or negative
- **THEN** the function SHALL raise a `ValueError`

#### Scenario: Negative vol
- **WHEN** `vol` is negative
- **THEN** the function SHALL raise a `ValueError`

#### Scenario: Non-positive discount factor
- **WHEN** `discount_factor` is zero or negative
- **THEN** the function SHALL raise a `ValueError`

### Requirement: Black76 implied vol inversion
The system SHALL provide a function `black76_implied_vol(price, forward, strike, discount_factor, expiry, is_call)` that returns the implied volatility by numerically inverting the Black76 formula.

#### Scenario: Round-trip call price to vol
- **WHEN** a call price is computed from known vol via `black76_call`, then `black76_implied_vol` is called with that price and `is_call=True`
- **THEN** the returned implied vol SHALL match the original vol within a tight tolerance (e.g., 1e-8)

#### Scenario: Round-trip put price to vol
- **WHEN** a put price is computed from known vol via `black76_put`, then `black76_implied_vol` is called with that price and `is_call=False`
- **THEN** the returned implied vol SHALL match the original vol within a tight tolerance

#### Scenario: Price below intrinsic value
- **WHEN** the supplied price is below the option's intrinsic value
- **THEN** the function SHALL raise a `ValueError` indicating a no-arbitrage violation

#### Scenario: Price above upper bound
- **WHEN** the call price exceeds `discount_factor * forward` or the put price exceeds `discount_factor * strike`
- **THEN** the function SHALL raise a `ValueError` indicating a no-arbitrage violation
