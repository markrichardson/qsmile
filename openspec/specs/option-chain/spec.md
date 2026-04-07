## ADDED Requirements

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
