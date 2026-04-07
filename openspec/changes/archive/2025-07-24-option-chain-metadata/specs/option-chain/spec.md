## MODIFIED Requirements

### Requirement: OptionChain stores market data
The system SHALL provide an `OptionChain` dataclass that holds strikes, call/put bid/ask prices, and a `metadata: SmileMetadata` field as its core fields. Strikes and prices SHALL be stored as NumPy arrays. The `metadata` parameter SHALL be a `SmileMetadata` instance provided by the caller at construction time. `expiry` on the metadata SHALL always be provided (not None). `forward` and `discount_factor` on the metadata MAY be None, in which case they SHALL be calibrated from put-call parity during `__post_init__`.

#### Scenario: Construct OptionChain with full metadata
- **WHEN** a user creates an `OptionChain` with strikes, call/put bid/ask arrays, and `metadata=SmileMetadata(expiry=0.25, forward=100.0, discount_factor=0.99)`
- **THEN** `chain.metadata.expiry` SHALL be 0.25, `chain.metadata.forward` SHALL be 100.0, and `chain.metadata.discount_factor` SHALL be 0.99

#### Scenario: Construct OptionChain with metadata needing calibration
- **WHEN** a user creates an `OptionChain` with `metadata=SmileMetadata(expiry=0.25)` (forward and discount_factor are None)
- **THEN** `chain.metadata.forward` and `chain.metadata.discount_factor` SHALL be calibrated from put-call parity and SHALL be positive floats (not None)

#### Scenario: Construct OptionChain with only forward needing calibration
- **WHEN** a user creates an `OptionChain` with `metadata=SmileMetadata(expiry=0.25, discount_factor=0.99)` (forward is None)
- **THEN** `chain.metadata.forward` SHALL be calibrated from put-call parity

#### Scenario: Non-positive expiry rejected
- **WHEN** the metadata's expiry is zero or negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: OptionChain validates inputs
The system SHALL validate option chain data on construction, rejecting invalid inputs with clear error messages.

#### Scenario: Mismatched array lengths
- **WHEN** any price array has a different length than strikes
- **THEN** the system SHALL raise a `ValueError` with a message indicating the length mismatch

#### Scenario: Non-positive strike
- **WHEN** any strike value is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Fewer than three data points
- **WHEN** the user supplies fewer than 3 strikes
- **THEN** the system SHALL raise a `ValueError`

## REMOVED Requirements

### Requirement: OptionChain computes log-moneyness
**Reason**: `OptionChain` no longer stores individual forward/expiry fields; log-moneyness is computed downstream via coordinate transforms on `SmileData`.
**Migration**: Use `SmileData` coordinate transforms after calling `to_smile_data()`.

### Requirement: OptionChain computes total variance
**Reason**: `OptionChain` no longer stores individual IV/expiry fields; total variance is computed downstream via coordinate transforms on `SmileData`.
**Migration**: Use `SmileData` coordinate transforms after calling `to_smile_data()`.
