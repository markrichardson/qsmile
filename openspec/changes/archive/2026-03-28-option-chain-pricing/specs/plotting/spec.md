## ADDED Requirements

### Requirement: OptionChainPrices provides a plot method
The system SHALL provide a `.plot()` method on `OptionChainPrices` that renders a figure with bid and ask prices shown as error bars at each strike. Calls and puts SHALL be distinguishable (e.g., different colours or markers).

#### Scenario: Plot prices
- **WHEN** `.plot()` is called on a valid `OptionChainPrices`
- **THEN** the system SHALL return a `matplotlib.figure.Figure` with error bars spanning bid to ask for both calls and puts

#### Scenario: Plot with custom title
- **WHEN** `.plot(title="My Plot")` is called
- **THEN** the figure SHALL use the supplied title

### Requirement: OptionChainVols provides a plot method
The system SHALL provide a `.plot()` method on `OptionChainVols` that renders a figure with bid and ask implied volatilities shown as error bars at each strike.

#### Scenario: Plot vols
- **WHEN** `.plot()` is called on a valid `OptionChainVols`
- **THEN** the system SHALL return a `matplotlib.figure.Figure` with error bars spanning vol_bid to vol_ask

#### Scenario: Plot with custom title
- **WHEN** `.plot(title="My Plot")` is called
- **THEN** the figure SHALL use the supplied title

### Requirement: UnitisedSpaceVols provides a plot method
The system SHALL provide a `.plot()` method on `UnitisedSpaceVols` that renders a figure with bid and ask total variances shown as error bars at each unitised log-moneyness point.

#### Scenario: Plot unitised space
- **WHEN** `.plot()` is called on a valid `UnitisedSpaceVols`
- **THEN** the system SHALL return a `matplotlib.figure.Figure` with error bars spanning variance_bid to variance_ask, plotted against unitised log-moneyness

#### Scenario: Plot with custom title
- **WHEN** `.plot(title="My Plot")` is called
- **THEN** the figure SHALL use the supplied title

### Requirement: Plot methods handle matplotlib import gracefully
The system SHALL raise an `ImportError` with a helpful message if `matplotlib` is not installed when `.plot()` is called.

#### Scenario: matplotlib not installed
- **WHEN** `.plot()` is called and `matplotlib` is not available
- **THEN** the system SHALL raise an `ImportError` with a message suggesting `pip install matplotlib`
