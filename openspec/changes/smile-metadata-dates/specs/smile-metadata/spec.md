## MODIFIED Requirements

### Requirement: SmileMetadata stores transform parameters
The system SHALL provide a `SmileMetadata` frozen dataclass with fields `date` (`pd.Timestamp`), `expiry` (`pd.Timestamp`), `daycount` (`DayCount`, default `DayCount.ACT365`), `forward` (`float | None`, default `None`), `discount_factor` (`float | None`, default `None`), and `sigma_atm` (`float | None`, default `None`). `date` and `expiry` SHALL be required. `expiry` SHALL be strictly after `date`. `forward`, `discount_factor`, and `sigma_atm`, when provided, SHALL be positive. The class SHALL expose a `texpiry` read-only property that returns `self.daycount.year_fraction(self.date, self.expiry)`. `forward` and `discount_factor` being `None` indicates they have not yet been calibrated.

#### Scenario: Construct SmileMetadata with all fields
- **WHEN** a user creates a `SmileMetadata` with `date=pd.Timestamp("2024-01-01")`, `expiry=pd.Timestamp("2024-04-01")`, `forward=100.0`, `discount_factor=0.99`, `sigma_atm=0.20`
- **THEN** all fields SHALL be stored and accessible as attributes, `texpiry` SHALL equal `DayCount.ACT365.year_fraction(date, expiry)`, and the object SHALL be immutable

#### Scenario: Construct SmileMetadata without sigma_atm
- **WHEN** a user creates a `SmileMetadata` with `date` and `expiry` timestamps, `forward=100.0`, `discount_factor=0.99`, and omits `sigma_atm`
- **THEN** `sigma_atm` SHALL be `None`

#### Scenario: Construct SmileMetadata with only dates
- **WHEN** a user creates a `SmileMetadata` with `date` and `expiry` timestamps only
- **THEN** `forward` SHALL be `None`, `discount_factor` SHALL be `None`, `sigma_atm` SHALL be `None`, `daycount` SHALL be `DayCount.ACT365`, and `texpiry` SHALL be the ACT/365 year fraction

#### Scenario: Construct SmileMetadata with ACT360 daycount
- **WHEN** a user creates a `SmileMetadata` with `date`, `expiry`, and `daycount=DayCount.ACT360`
- **THEN** `texpiry` SHALL equal `(expiry - date).days / 360.0`

#### Scenario: Non-positive forward rejected
- **WHEN** `forward` is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: None forward accepted
- **WHEN** `forward` is `None`
- **THEN** the system SHALL accept the value without error

#### Scenario: Non-positive discount_factor rejected
- **WHEN** `discount_factor` is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: None discount_factor accepted
- **WHEN** `discount_factor` is `None`
- **THEN** the system SHALL accept the value without error

#### Scenario: Expiry not after date rejected
- **WHEN** `expiry` is equal to or before `date`
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive sigma_atm rejected
- **WHEN** `sigma_atm` is provided and is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: SmileMetadata is immutable
- **WHEN** a user attempts to modify any attribute of a `SmileMetadata` instance
- **THEN** the system SHALL raise a `FrozenInstanceError`

#### Scenario: texpiry is a derived property
- **WHEN** a user accesses `metadata.texpiry`
- **THEN** the value SHALL equal `metadata.daycount.year_fraction(metadata.date, metadata.expiry)`
