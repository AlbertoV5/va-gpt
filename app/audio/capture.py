from typing import NamedTuple
from torch import Tensor


class Capture(NamedTuple):
    """Carries torch Tensor and its metadata.

    Attributes:
        data (torch.Tensor): Audio data as Tensor.
        size (int): Sample size.
        sr (int): Sample rate.
        dbpeak (float): Peak in decibels.
        dbrms (float): RMS in decibels.
    """

    data: Tensor
    size: int
    sr: int
    dbpeak: float
    dbrms: float

    def __repr__(self):
        return (
            f"Capture({self.dbpeak:.1f} db, {self.dbrms:.1f} rms, {(self.size / self.sr):.1f} s)"
        )
