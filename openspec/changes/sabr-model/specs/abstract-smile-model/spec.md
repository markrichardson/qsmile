## ADDED Requirements

### Requirement: AbstractSmileModel provides default to_array
`AbstractSmileModel` SHALL provide a default `to_array()` implementation that packs the values of all fields listed in `param_names` into a NumPy float64 array, in the order they appear in `param_names`.

#### Scenario: to_array uses param_names ordering
- **WHEN** `to_array()` is called on a subclass instance
- **THEN** the result SHALL be a NumPy array containing the values of fields listed in `param_names`, in order

### Requirement: AbstractSmileModel provides default from_array
`AbstractSmileModel` SHALL provide a default `from_array(x)` classmethod that reconstructs an instance by mapping array elements to the fields listed in `param_names`, in order.

#### Scenario: from_array reconstructs instance
- **WHEN** `SubClass.from_array(arr)` is called with an array
- **THEN** the result SHALL be an instance of `SubClass` with fields set from the array values

#### Scenario: from_array is a classmethod returning Self
- **WHEN** `from_array()` is called on a subclass
- **THEN** the return type SHALL be an instance of that subclass, not `AbstractSmileModel`

### Requirement: AbstractSmileModel is abstract
`AbstractSmileModel` SHALL be an abstract dataclass. Concrete subclasses MUST define `native_x_coord`, `native_y_coord`, `param_names`, `bounds`, `evaluate()`, and `initial_guess()`.

#### Scenario: Cannot instantiate AbstractSmileModel directly
- **WHEN** a user attempts to instantiate `AbstractSmileModel()` directly
- **THEN** a `TypeError` SHALL be raised

### Requirement: AbstractSmileModel subclasses satisfy SmileModel protocol
Any concrete subclass of `AbstractSmileModel` that defines all required ClassVars and methods SHALL satisfy the `SmileModel` protocol.

#### Scenario: Concrete subclass passes isinstance check
- **WHEN** a concrete subclass instance is checked against `SmileModel`
- **THEN** `isinstance(instance, SmileModel)` SHALL return `True`
