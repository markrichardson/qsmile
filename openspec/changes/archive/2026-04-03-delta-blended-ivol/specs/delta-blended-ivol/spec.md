## ADDED Requirements

### Requirement: Delta-blended implied vol computation
The system SHALL provide a function `delta_blend_ivols(call_ivols, put_ivols, strikes, forward, expiry)` that returns blended implied volatilities at each strike using Black76 undiscounted call-delta weighting. The blended vol at strike $K$ SHALL be $\sigma(K) = w(K)\,\sigma_C(K) + (1-w(K))\,\sigma_P(K)$ where $w(K) = \Phi(d_1)$ and $d_1 = [\ln(F/K) + \tfrac{1}{2}\sigma_C^2 t] / (\sigma_C \sqrt{t})$.

#### Scenario: ATM blending is equal-weighted
- **WHEN** `delta_blend_ivols` is called with `forward == strike` and identical call/put vols
- **THEN** the blended vol at the ATM strike SHALL equal the call vol (and put vol), and the delta weight SHALL be approximately 0.5

#### Scenario: Deep OTM call converges to call vol
- **WHEN** strike is far below the forward (deep ITM put / deep OTM call wing)
- **THEN** the delta weight $w(K)$ SHALL approach 1.0 and the blended vol SHALL converge to the call-implied vol

#### Scenario: Deep OTM put converges to put vol
- **WHEN** strike is far above the forward (deep OTM put / deep ITM call wing)
- **THEN** the delta weight $w(K)$ SHALL approach 0.0 and the blended vol SHALL converge to the put-implied vol

#### Scenario: Smooth blending across all strikes
- **WHEN** `delta_blend_ivols` is called with any valid inputs
- **THEN** the delta weights SHALL vary smoothly (monotonically decreasing in strike) with no discontinuities

### Requirement: Bid/ask blending uses same delta weights
The system SHALL blend bid vols and ask vols independently using the same delta weights computed from the mid call-implied vol at each strike. This ensures the output spread reflects the liquidity-weighted market spread.

#### Scenario: Independent bid/ask blending
- **WHEN** `delta_blend_ivols` is called with separate bid and ask arrays for calls and puts
- **THEN** the blended bid and ask SHALL each be computed as $w \cdot \text{call} + (1-w) \cdot \text{put}$ using the same weight vector $w$

### Requirement: Graceful handling of inversion failure
The system SHALL handle strikes where one option type's implied vol cannot be computed (e.g., price below intrinsic). At such strikes, the blended vol SHALL fall back to the vol from the other option type. If neither can be inverted, the strike SHALL be excluded from the output.

#### Scenario: Call vol unavailable at a strike
- **WHEN** the call price at a strike cannot be inverted to a vol
- **THEN** the blended vol at that strike SHALL equal the put-implied vol (weight forced to 0)

#### Scenario: Put vol unavailable at a strike
- **WHEN** the put price at a strike cannot be inverted to a vol
- **THEN** the blended vol at that strike SHALL equal the call-implied vol (weight forced to 1)

#### Scenario: Neither vol available
- **WHEN** neither call nor put price can be inverted at a strike
- **THEN** that strike SHALL be excluded from the returned arrays
