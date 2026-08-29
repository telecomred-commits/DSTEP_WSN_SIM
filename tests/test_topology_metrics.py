from wsn_sim.topology.metrics import topology_metrics
class N:
 def __init__(self,x,y): self.position=(x,y)
def test_topology_connectivity_and_sensing():
 m=topology_metrics([N(0,0),N(1,0),N(50,0)],5,[100,100],10)
 assert m["isolated_nodes"]==1; assert m["connected_components"]==2; assert abs(m["largest_component_fraction"]-2/3)<1e-9; assert 0<=m["estimated_sensing_coverage_fraction"]<=1
