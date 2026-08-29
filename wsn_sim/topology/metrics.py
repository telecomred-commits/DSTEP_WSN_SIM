import math

def _mean(xs):
    return sum(xs)/len(xs) if xs else None

def estimate_sensing_coverage(nodes,sensing_radius_m,area_m,grid_n=40):
    if not nodes or sensing_radius_m is None or sensing_radius_m<=0:
        return 0.0
    w,h=area_m
    covered=0
    total=grid_n*grid_n
    for iy in range(grid_n):
        y=(iy+0.5)*h/grid_n
        for ix in range(grid_n):
            x=(ix+0.5)*w/grid_n
            if any(math.dist((x,y),n.position)<=sensing_radius_m for n in nodes):
                covered+=1
    return covered/total

def topology_metrics(nodes, *args, **kwargs):
    """
    New API:
      topology_metrics(nodes, area_m, sensing_radius_m=None,
                       link_predicate=..., link_margin_fn=...)

    Legacy API retained:
      topology_metrics(nodes, neighbor_radius_m, area_m, sensing_radius_m=None)
    """
    link_predicate = kwargs.get("link_predicate")
    link_margin_fn = kwargs.get("link_margin_fn")

    if args and isinstance(args[0], (int,float)):
        # Legacy form
        neighbor_radius_m = float(args[0])
        area_m = args[1]
        sensing_radius_m = args[2] if len(args) > 2 else None
        if link_predicate is None:
            link_predicate = lambda a,b: math.dist(a.position,b.position) <= neighbor_radius_m
    else:
        area_m = args[0] if args else kwargs["area_m"]
        sensing_radius_m = args[1] if len(args) > 1 else kwargs.get("sensing_radius_m")

    n=len(nodes)
    if not n:
        return {}

    adjacency={i:[] for i in range(n)}
    pair=[]; neighbor_d=[]; nearest=[]; margins=[]

    for i in range(n):
        ds=[]
        for j in range(n):
            if i==j:
                continue
            d=math.dist(nodes[i].position,nodes[j].position)
            ds.append(d)
            if j>i:
                pair.append(d)
            connected = bool(link_predicate(nodes[i],nodes[j])) if link_predicate else False
            if connected:
                adjacency[i].append(j)
                if j>i:
                    neighbor_d.append(d)
                    if link_margin_fn:
                        margins.append(link_margin_fn(nodes[i],nodes[j]))
        nearest.append(min(ds) if ds else 0.0)

    deg=[len(adjacency[i]) for i in range(n)]
    seen=set(); comps=[]
    for i in range(n):
        if i in seen:
            continue
        stack=[i]; size=0
        while stack:
            u=stack.pop()
            if u in seen:
                continue
            seen.add(u); size+=1; stack.extend(adjacency[u])
        comps.append(size)

    w,h=area_m
    area=max(w*h,1e-9)
    out={
        "node_density_per_m2": n/area,
        "mean_nearest_neighbor_m": _mean(nearest),
        "mean_neighbor_distance_m": _mean(neighbor_d),
        "mean_pair_distance_m": _mean(pair),
        "mean_degree": _mean(deg),
        "min_degree": min(deg),
        "max_degree": max(deg),
        "isolated_nodes": sum(d==0 for d in deg),
        "connected_components": len(comps),
        "largest_component_fraction": max(comps)/n if comps else 0.0,
        "mean_nominal_link_margin_db": _mean(margins),
        "min_nominal_link_margin_db": min(margins) if margins else None,
        "max_nominal_link_margin_db": max(margins) if margins else None,
    }
    if sensing_radius_m is not None:
        out["sensing_radius_m"]=sensing_radius_m
        out["estimated_sensing_coverage_fraction"]=estimate_sensing_coverage(nodes,sensing_radius_m,area_m)
    return out
