## ADDED Requirements

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

### Requirement: OptionChain denoise preserves volume and open interest
The `denoise()` method SHALL propagate `volume` and `open_interest` arrays to the returned `OptionChain`, subsetting them with the same mask used to filter strikes. If the source arrays are `None`, the returned chain's arrays SHALL also be `None`.

#### Scenario: Denoise subsets volume and open interest
- **WHEN** `denoise()` is called on an `OptionChain` with `volume` and `open_interest`
- **THEN** the returned chain's `volume` and `open_interest` SHALL contain only the entries corresponding to the surviving strikes

#### Scenario: Denoise with None volume and open interest
- **WHEN** `denoise()` is called on an `OptionChain` where `volume` and `open_interest` are `None`
- **THEN** the returned chain's `volume` and `open_interest` SHALL be `None`
