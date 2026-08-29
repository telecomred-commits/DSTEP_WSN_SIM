from .free_space import FreeSpaceChannel
from .log_distance import LogDistanceChannel
from .log_normal import LogNormalChannel
from .two_ray import TwoRayGroundChannel
from .rayleigh import RayleighChannel
from .rician import RicianChannel
from .nakagami import NakagamiChannel
CHANNELS={"free_space":FreeSpaceChannel,"log_distance":LogDistanceChannel,"log_normal":LogNormalChannel,"two_ray":TwoRayGroundChannel,"rayleigh":RayleighChannel,"rician":RicianChannel,"nakagami":NakagamiChannel}
def create_channel(name,cfg,rng):
    try: cls=CHANNELS[name]
    except KeyError: raise ValueError(f"Unknown channel model: {name}. Available: {sorted(CHANNELS)}")
    return cls(cfg,rng)
