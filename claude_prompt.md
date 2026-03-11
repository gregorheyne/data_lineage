can you make the following changes to this network_base.py file:

The function register_node() gets an additional keyword argument called 'target_node' with default False

If 'target_node' is passed as False for a register_node() call, then the if-else statement with _node_known(node_name) == True and _node_known(node_name) == False should be handled as follows:
In the case _node_known(node_name) == True, the current logic should not change, i.e. a simple check if type of the registered node is the same as type of the new observation of this node.
In the case _node_known(node_name) == False the metaddict should be augmented with the attribute 'seen_as_target' set to False before passing it into _add_new_node. more precisely make a copy of the passed metadict and add 'seen_as_target': False to this copy and then pass this copy into _add_new_node

If 'target_node' is passed as True for a register_node() call, then the if-else statement with _node_known(node_name) == True and _node_known(node_name) == False should be handled as follows:
In the case _node_known(node_name) == True, there should be the following additional logic after the assert statemment in this block:
- check the seen_as_target attribute of the known (already registered) node.
- if seen_as_target == True, do nothing further
- if seen_as_target == False, update the the node attributes as follows: keep and dont change the attributes id, name, and type. remove the remaining attributes. add the additional attributes found in the meta_dict that is passed into register_node as well as adding 'seen_as_target': True.
In the case _node_known(node_name) == False the metaddict should be augmented with the attribute 'seen_as_target': True before passing it into _add_new_node. more precisely make a copy of the passed metadict and add 'seen_as_target': True to this copy and then pass this copy into _add_new_node