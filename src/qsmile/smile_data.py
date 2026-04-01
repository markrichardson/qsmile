"""Unified smile data container with coordinate transforms."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from qsmile.coords import XCoord, YCoord
from qsmile.maps import (
    apply_x_chain,
    apply_y_chain,
    compose_x_maps,
    compose_y_maps,
)
from qsmile.metadata import SmileMetadata


@dataclass
class SmileData:
    """Coordinate-labelled smile data with bid/ask.

    Parameters
    ----------
    x : NDArray[np.float64]
        X-coordinate values.
    y_bid : NDArray[np.float64]
        Y-coordinate bid values.
    y_ask : NDArray[np.float64]
        Y-coordinate ask values.
    x_coord : XCoord
        Which X-coordinate system the data is in.
    y_coord : YCoord
        Which Y-coordinate system the data is in.
    metadata : SmileMetadata
        Parameters needed by coordinate transforms.
    """

    x: NDArray[np.float64]
    y_bid: NDArray[np.float64]
    y_ask: NDArray[np.float64]
    x_coord: XCoord
    y_coord: YCoord
    metadata: SmileMetadata

    def __post_init__(self) -> None:
        """Validate and convert inputs."""
        self.x = np.asarray(self.x, dtype=np.float64)
        self.y_bid = np.asarray(self.y_bid, dtype=np.float64)
        self.y_ask = np.asarray(self.y_ask, dtype=np.float64)

        n = len(self.x)
        if len(self.y_bid) != n or len(self.y_ask) != n:
            msg = (
                f"all arrays must have the same length as x ({n}), got y_bid={len(self.y_bid)}, y_ask={len(self.y_ask)}"
            )
            raise ValueError(msg)

    @property
    def y_mid(self) -> NDArray[np.float64]:
        """Midpoint of bid and ask Y values."""
        return (self.y_bid + self.y_ask) / 2.0

    def transform(self, target_x: XCoord, target_y: YCoord) -> SmileData:
        """Re-express data in target coordinate system.

        Parameters
        ----------
        target_x : XCoord
            Target X-coordinate system.
        target_y : YCoord
            Target Y-coordinate system.

        Returns:
        -------
        SmileData
            New SmileData in the target coordinates.
        """
        # Transform X
        x_chain = compose_x_maps(self.x_coord, target_x)
        new_x = apply_x_chain(self.x, x_chain, self.metadata)

        # Transform Y (bid and ask independently)
        y_chain = compose_y_maps(self.y_coord, target_y)
        new_y_bid = apply_y_chain(self.y_bid, self.x, y_chain, self.metadata, self.x_coord, target_x)
        new_y_ask = apply_y_chain(self.y_ask, self.x, y_chain, self.metadata, self.x_coord, target_x)

        return SmileData(
            x=new_x,
            y_bid=new_y_bid,
            y_ask=new_y_ask,
            x_coord=target_x,
            y_coord=target_y,
            metadata=self.metadata,
        )
