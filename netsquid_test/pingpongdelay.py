from netsquid.components.models import DelayModel

class PingPongDelayModel(DelayModel):
    def __init__(self, c_fraction=0.5, stdev=0.05):
        super().__init__()
        # speed of light = 300,000 km/s
        self.properties["speed"] = c_fraction * 3e5
        self.properties["std"] = stdev
        self.required_properties = ['length'] # in km

    def generate_delay(self, **kwargs):
        avg_speed = self.properties["speed"]
        std = self.properties["std"]
        # generate random speed using "rnd" property
        speed = self.properties["rng"].normal(avg_speed, avg_speed*std)
        delay = 1e9 * kwargs["length"] / speed # in ns
        return delay