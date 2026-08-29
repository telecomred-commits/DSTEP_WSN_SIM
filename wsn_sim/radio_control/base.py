class RadioController:
    name = "base"

    def __init__(self, sim):
        self.sim = sim
        self.cfg = sim.cfg.get("radio_control", {})

    def initialize_node(self, node):
        initial = float(self.cfg.get("initial_tx_power_dbm", self.sim.radio_cfg.get("tx_power_dbm", 0.0)))
        node.tx_power_dbm = initial
        node.last_tx_power_dbm = initial
        node.tx_power_history = [initial]

    def before_transmit(self, node):
        return node.tx_power_dbm

    def transmission_directive(self, node):
        # Default: transmit now.
        return {"transmit": True, "delay_s": 0.0, "reason": "immediate"}

    def after_transmit(self, node, feedback):
        pass

    def set_power(self, node, power_dbm):
        levels = sorted(float(x) for x in self.cfg.get("power_levels_dbm", [power_dbm]))
        chosen = min(levels, key=lambda p: abs(p - float(power_dbm)))
        old = node.tx_power_dbm
        node.last_tx_power_dbm = old
        node.tx_power_dbm = chosen

        if chosen != old:
            node.radio_power_changes += 1
            if chosen > old:
                node.radio_power_increases += 1
            else:
                node.radio_power_decreases += 1
            node.tx_power_history.append(chosen)
        return chosen
