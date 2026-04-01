## ADDED Requirements

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

## REMOVED Requirements

### Requirement: OptionChainVols provides a plot method
**Reason**: `OptionChainVols` is removed. Plot functionality is replaced by `SmileData.plot()`.
**Migration**: Use `SmileData.plot()` on a SmileData with `(FixedStrike, Volatility)` coordinates.

### Requirement: UnitisedSpaceVols provides a plot method
**Reason**: `UnitisedSpaceVols` is removed. Plot functionality is replaced by `SmileData.plot()`.
**Migration**: Use `SmileData.plot()` on a SmileData with `(StandardisedStrike, TotalVariance)` coordinates.
