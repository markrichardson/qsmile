"""Smile metadata for coordinate transforms."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SmileMetadata:
    """Parameters needed by coordinate transforms.

    Parameters
    ----------
    forward : float | None
        Forward price. Must be positive when provided.
    discount_factor : float | None
        Discount factor. Must be positive when provided.
    expiry : float
        Time to expiry in years. Must be positive.
    sigma_atm : float | None
        ATM implied volatility. Must be positive when provided.
        Required for StandardisedStrike transforms.
    """

    expiry: float
    forward: float | None = None
    discount_factor: float | None = None
    sigma_atm: float | None = None

    def __post_init__(self) -> None:
        """Validate inputs."""
        if self.expiry <= 0:
            msg = f"expiry must be positive, got {self.expiry}"
            raise ValueError(msg)
        if self.forward is not None and self.forward <= 0:
            msg = f"forward must be positive, got {self.forward}"
            raise ValueError(msg)
        if self.discount_factor is not None and self.discount_factor <= 0:
            msg = f"discount_factor must be positive, got {self.discount_factor}"
            raise ValueError(msg)
        if self.sigma_atm is not None and self.sigma_atm <= 0:
            msg = f"sigma_atm must be positive, got {self.sigma_atm}"
            raise ValueError(msg)
