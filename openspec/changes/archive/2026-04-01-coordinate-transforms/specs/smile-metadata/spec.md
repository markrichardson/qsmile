## ADDED Requirements

### Requirement: SmileMetadata stores transform parameters
The system SHALL provide a `SmileMetadata` frozen dataclass with fields `forward` (float), `discount_factor` (float), `expiry` (float), and `sigma_atm` (float | None, default None). All numeric fields except `sigma_atm` SHALL be required and positive. `sigma_atm`, when provided, SHALL be positive.

#### Scenario: Construct SmileMetadata with all fields
- **WHEN** a user creates a `SmileMetadata` with forward=100.0, discount_factor=0.99, expiry=0.25, sigma_atm=0.20
- **THEN** all fields SHALL be stored and accessible as attributes, and the object SHALL be immutable

#### Scenario: Construct SmileMetadata without sigma_atm
- **WHEN** a user creates a `SmileMetadata` with forward=100.0, discount_factor=0.99, expiry=0.25 and omits sigma_atm
- **THEN** sigma_atm SHALL be None

#### Scenario: Non-positive forward rejected
- **WHEN** forward is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive discount_factor rejected
- **WHEN** discount_factor is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive expiry rejected
- **WHEN** expiry is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Non-positive sigma_atm rejected
- **WHEN** sigma_atm is provided and is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: SmileMetadata is immutable
- **WHEN** a user attempts to modify any attribute of a SmileMetadata instance
- **THEN** the system SHALL raise a `FrozenInstanceError`
