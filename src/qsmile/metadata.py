"""Smile metadata for coordinate transforms."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SmileMetadata:
    """Parameters needed by coordinate transforms.

    Parameters
    ----------
    forward : float
        Forward price. Must be positive.
    discount_factor : float
        Discount factor. Must be positive.
    expiry : float
        Time to expiry in years. Must be positive.
    sigma_atm : float | None
        ATM implied volatility. Must be positive when provided.
        Required for StandardisedStrike transforms.
    """

    forward: float
    discount_factor: float
    expiry: float
    sigma_atm: float | None = None

    def __post_init__(self) -> None:
        """Validate inputs."""
        if self.forward <= 0:
            msg = f"forward must be positive, got {self.forward}"
            raise ValueError(msg)
        if self.discount_factor <= 0:
            msg = f"discount_factor must be positive, got {self.discount_factor}"
            raise ValueError(msg)
        if self.expiry <= 0:
            msg = f"expiry must be positive, got {self.expiry}"
            raise ValueError(msg)
        if self.sigma_atm is not None and self.sigma_atm <= 0:
            msg = f"sigma_atm must be positive, got {self.sigma_atm}"
            raise ValueError(msg)
