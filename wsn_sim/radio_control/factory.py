from .fixed import FixedPowerController
from .rule_based import RuleBasedAdaptivePowerController
from .channel_aware import ChannelAwareAdaptiveRadioController

CONTROLLERS = {
    "fixed": FixedPowerController,
    "rule_based_adaptive": RuleBasedAdaptivePowerController,
    "channel_aware_adaptive": ChannelAwareAdaptiveRadioController,
}

def create_radio_controller(name, sim):
    if name not in CONTROLLERS:
        raise ValueError(f"Unknown radio controller: {name}")
    return CONTROLLERS[name](sim)
