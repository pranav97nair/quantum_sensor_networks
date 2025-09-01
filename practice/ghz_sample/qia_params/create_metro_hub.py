from netsquid_netbuilder.modules.clinks import DefaultCLinkConfig
from netsquid_netbuilder.modules.qlinks import DepolariseQLinkConfig
from netsquid_netbuilder.modules.qdevices import GenericQDeviceConfig
from netsquid_netbuilder.modules.scheduler import FIFOScheduleConfig
from netsquid_netbuilder.util.network_generation import create_metro_hub_network


# Network options
num_nodes = 5
use_high_fidelity = True
use_optimistic = True
# scheduler_multiplexing determines many entanglement generation processes can run in parallel via the metro hub
scheduler_multiplexing = 1
# scheduler_switch_time determines long it takes to change the nodes engaging in entanglement generation via the hub
scheduler_switch_time = 1000  # 1 us

if use_optimistic:
    postfix = "_optimistic"
else:
    postfix = "_current"

postfix_link = postfix

if use_high_fidelity:
    postfix_link += "_high_fid"


# Load configuration from YAML file
qlink_cfg = DepolariseQLinkConfig.from_file(f"link_params{postfix_link}.yaml")
qdevice_cfg = GenericQDeviceConfig.from_file(f"qdevice_params{postfix}.yaml")
# Create clink cfg, link cfg options assume speed of light in fibres of 200_000 km/s
clink_cfg = DefaultCLinkConfig(speed_of_light=200_000, length=None)
schedule_cfg = FIFOScheduleConfig(max_multiplexing=scheduler_multiplexing, switch_time=scheduler_switch_time)

# The metro hub will set the distance, so we can't manually specify that the cycle time is 325 us
# If we leave the speed_of_light at 200,000 km/s it will create a cycle time of 250 us,
# So we modify the speed of light (only for the entanglement generation model)
qlink_cfg.t_cycle = None
qlink_cfg.speed_of_light = 200_000 * 250 / 325

node_names = [f"node_{i}" for i in range(num_nodes)]
# qlink config parameters assume 50 km distance between nodes (and heralding station/hub halfway)
node_distances = [25 for _ in range(num_nodes)]

network_cfg = create_metro_hub_network(node_names, node_distances,
                                       qlink_typ="depolarise", qlink_cfg=qlink_cfg,
                                       clink_typ="default", clink_cfg=clink_cfg,
                                       qdevice_typ="generic", qdevice_cfg=qdevice_cfg,
                                       schedule_typ="fifo", schedule_cfg=schedule_cfg)


