## Requirements

### Requirement: OptionChain provides a plot method
The system SHALL provide a `.plot()` method on `OptionChain` that renders a figure with bid and ask prices shown as error bars at each strike. Calls and puts SHALL be distinguishable (e.g., different colours or markers).

#### Scenario: Plot prices
- **WHEN** `.plot()` is called on a valid `OptionChain`
- **THEN** the system SHALL return a `matplotlib.figure.Figure` with error bars spanning bid to ask for both calls and puts

#### Scenario: Plot with custom title
- **WHEN** `.plot(title="My Plot")` is called
- **THEN** the figure SHALL use the supplied title

### Requirement: SmileData provides a plot method
The system SHALL provide a `.plot()` method on `SmileData` that renders a figure with bid and ask Y-values shown as error bars at each X point. Axis labels SHALL be derived from the `x_coord` and `y_coord` names.

#### Scenario: Plot SmileData in volatility coordinates
- **WHEN** `.plot()` is called on a `SmileData` with `(FixedStrike, Volatility)` coordinates
- **THEN** the system SHALL return a `matplotlib.figure.Figure` with X-axis labelled "FixedStrike" and Y-axis labelled "Volatility"

#### Scenario: Plot SmileData in unitised coordinates
- **WHEN** `.plot()` is called on a `SmileData` with `(StandardisedStrike, TotalVariance)` coordinates
- **THEN** the system SHALL return a `matplotlib.figure.Figure` with appropriate axis labels

#### Scenario: Plot with custom title
- **WHEN** `.plot(title="My Plot")` is called on a `SmileData`
- **THEN** the figure SHALL use the supplied title

### Requirement: Plot methods handle matplotlib import gracefully
The system SHALL raise an `ImportError` with a helpful message if `matplotlib` is not installed when `.plot()` is called.

#### Scenario: matplotlib not installed
- **WHEN** `.plot()` is called and `matplotlib` is not available
- **THEN** the system SHALL raise an `ImportError` with a message suggesting `pip install matplotlib`
