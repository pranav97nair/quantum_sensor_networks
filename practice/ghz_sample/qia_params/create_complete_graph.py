from squidasm.util.util import create_complete_graph_network # type: ignore
from squidasm.run.stack.config import DepolariseLinkConfig, DefaultCLinkConfig, GenericQDeviceConfig # type: ignore


# Network options
num_nodes = 5
use_high_fidelity = True
use_optimistic = True

if use_optimistic:
    postfix = "_optimistic"
else:
    postfix = "_current"

postfix_link = postfix

if use_high_fidelity:
    postfix_link += "_high_fid"

# Load configuration from YAML file
link_cfg = DepolariseLinkConfig.from_file(f"link_params{postfix_link}.yaml")
qdevice_cfg = GenericQDeviceConfig.from_file(f"qdevice_params{postfix}.yaml")
# Create clink cfg, link cfg options assume 50 km separation and speed of light in fibres of 200_000 km/s
clink_cfg = DefaultCLinkConfig(speed_of_light=200_000, length=50)


node_names = [f"node_{i}" for i in range(num_nodes)]

network_cfg = create_complete_graph_network(node_names,
                                            link_typ="depolarise", link_cfg=link_cfg,
                                            clink_typ="default", clink_cfg=clink_cfg,
                                            qdevice_typ="generic", qdevice_cfg=qdevice_cfg)
