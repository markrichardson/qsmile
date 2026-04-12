## ADDED Requirements

### Requirement: Model provides plot method
`AbstractSmileModel` SHALL provide a `plot()` method that generates a matplotlib Figure showing the model's curve in its current coordinate system.

#### Scenario: Plot model in native coordinates
- **WHEN** `model.plot()` is called on a model in native coordinates
- **THEN** a matplotlib Figure SHALL be returned with x-axis labelled with the native x-coord name and y-axis labelled with the native y-coord name

#### Scenario: Plot model in transformed coordinates
- **WHEN** `model.transform(XCoord.FixedStrike, YCoord.Volatility).plot()` is called
- **THEN** the Figure SHALL show the model curve in FixedStrike × Volatility space with appropriate axis labels

#### Scenario: Plot accepts title parameter
- **WHEN** `model.plot(title="My Smile")` is called
- **THEN** the Figure SHALL have "My Smile" as its title

#### Scenario: Plot generates evaluation grid automatically
- **WHEN** `model.plot()` is called without explicit x values
- **THEN** the method SHALL generate a suitable grid of x values covering the relevant domain
