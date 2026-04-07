## MODIFIED Requirements

### Requirement: OptionChain stores market data
The system SHALL provide an `OptionChain` dataclass that holds strikes, call/put bid/ask prices, and a `metadata: SmileMetadata` field as its core fields. Strikes and prices SHALL be stored as NumPy arrays. The `metadata` parameter SHALL be a `SmileMetadata` instance provided by the caller at construction time. `date` and `expiry` on the metadata SHALL always be provided as `pd.Timestamp` values. `forward` and `discount_factor` on the metadata MAY be `None`, in which case they SHALL be calibrated from put-call parity during `__post_init__`.

#### Scenario: Construct OptionChain with full metadata
- **WHEN** a user creates an `OptionChain` with strikes, call/put bid/ask arrays, and `metadata=SmileMetadata(date=pd.Timestamp("2024-01-01"), expiry=pd.Timestamp("2024-04-01"), forward=100.0, discount_factor=0.99)`
- **THEN** `chain.metadata.texpiry` SHALL be the ACT/365 year fraction, `chain.metadata.forward` SHALL be `100.0`, and `chain.metadata.discount_factor` SHALL be `0.99`

#### Scenario: Construct OptionChain with metadata needing calibration
- **WHEN** a user creates an `OptionChain` with `metadata=SmileMetadata(date=pd.Timestamp("2024-01-01"), expiry=pd.Timestamp("2024-04-01"))` (forward and discount_factor are `None`)
- **THEN** `chain.metadata.forward` and `chain.metadata.discount_factor` SHALL be calibrated from put-call parity and SHALL be positive floats (not `None`)

#### Scenario: Construct OptionChain with only forward needing calibration
- **WHEN** a user creates an `OptionChain` with `metadata=SmileMetadata(date=pd.Timestamp("2024-01-01"), expiry=pd.Timestamp("2024-04-01"), discount_factor=0.99)` (forward is `None`)
- **THEN** `chain.metadata.forward` SHALL be calibrated from put-call parity

#### Scenario: Expiry not after date rejected
- **WHEN** the metadata's `expiry` is equal to or before `date`
- **THEN** the system SHALL raise a `ValueError`
