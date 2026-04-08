## ADDED Requirements

### Requirement: from_mid_vols accepts SmileMetadata directly
The system SHALL allow `SmileData.from_mid_vols` to accept a `metadata: SmileMetadata` parameter as an alternative to the individual `forward`, `date`, `expiry`, `discount_factor`, and `daycount` parameters. When `metadata` is provided, the factory SHALL use `metadata.forward` for ATM derivation and populate the returned `SmileData.metadata` using the passed `SmileMetadata` (with `sigma_atm` recomputed from the data).

#### Scenario: Construct from SmileMetadata
- **WHEN** `SmileData.from_mid_vols(strikes, ivs, metadata=SmileMetadata(date=..., expiry=..., forward=100.0, discount_factor=0.99))` is called
- **THEN** the returned `SmileData` SHALL have `metadata.forward == 100.0`, `metadata.discount_factor == 0.99`, and `sigma_atm` derived from the ATM strike

#### Scenario: sigma_atm recomputed from data
- **WHEN** `SmileData.from_mid_vols` is called with a `metadata` that has `sigma_atm=0.5`
- **THEN** the returned `SmileData.metadata.sigma_atm` SHALL be recomputed from `ivs` at the ATM strike, not `0.5`

#### Scenario: metadata.forward required
- **WHEN** `SmileData.from_mid_vols` is called with `metadata=SmileMetadata(date=..., expiry=..., forward=None)`
- **THEN** a `TypeError` SHALL be raised indicating that `forward` is required

#### Scenario: metadata takes precedence over scalar params
- **WHEN** both `metadata` and scalar `forward`/`date`/`expiry` parameters are provided
- **THEN** the `metadata` values SHALL be used and scalar parameters SHALL be ignored
