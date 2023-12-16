from frost_mpc.common.configuration_settings import ConfigurationSettings
from frost_mpc.node import Node
from node_info import NodeInfo
from data_manager import NodeDataManager
from validators import NodeValidators
from node_confg import SECRETS

import trio
import sys

async def run_node(node_number: int) -> None:
    data_manager = NodeDataManager()
    node_info = NodeInfo()
    node_peer_id = node_info.get_all_nodes()[node_number]
    node = Node(data_manager, node_info.lookup_node(node_peer_id), SECRETS[node_peer_id], node_info, 
                    NodeValidators.caller_validator, NodeValidators.data_validator)
    await node.run()

if __name__ == '__main__':
    ConfigurationSettings.set_logging_options \
                        ('logs', f'node{sys.argv[1]}.log')
    sys.set_int_max_str_digits(0)
    node_number = int(sys.argv[1])
    try:
        trio.run(run_node, node_number)
    except KeyboardInterrupt:
        pass