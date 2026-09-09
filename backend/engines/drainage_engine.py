"""Drainage network graph engine for capacity, flow utilization, blockage, and surcharge modeling."""
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx

from backend.models.drainage_models import (
    DrainStatus,
    DrainageEdgeMetrics,
    DrainageEdgeModel,
    DrainageNetworkResponse,
    DrainageNetworkSummary,
    DrainageNodeModel,
)
from backend.services.drainage_service import (
    DrainageService,
    InvalidDrainageDataFormatError,
    default_drainage_service,
)


class DrainageEngine:
    """Core computational graph engine modeling urban pipe hydraulics, bottlenecks, and surcharge."""

    def __init__(self, service: Optional[DrainageService] = None):
        self.service = service or default_drainage_service
        self._graph: Optional[nx.DiGraph] = None
        self._edge_lookup: Dict[str, Tuple[str, str]] = {}

    @staticmethod
    def classify_drain_status(utilization_percent: float) -> DrainStatus:
        """
        Centralized threshold rules for conduit utilization status:
        < 70%       -> NORMAL
        70% - 90%   -> WARNING
        90% - 100%  -> CRITICAL
        > 100%      -> SURCHARGED
        """
        if utilization_percent < 70.0:
            return DrainStatus.NORMAL
        elif utilization_percent < 90.0:
            return DrainStatus.WARNING
        elif utilization_percent <= 100.0:
            return DrainStatus.CRITICAL
        else:
            return DrainStatus.SURCHARGED

    @staticmethod
    def calculate_effective_capacity(capacity_m3s: float, blockage_percent: float) -> float:
        """Calculates available capacity after accounting for sediment or obstruction blockage."""
        factor = max(0.0, min(1.0, 1.0 - (blockage_percent / 100.0)))
        return round(max(0.0, capacity_m3s * factor), 4)

    @staticmethod
    def calculate_utilization(current_flow_m3s: float, effective_capacity_m3s: float) -> float:
        """Calculates conduit capacity utilization percentage with division-by-zero protection."""
        if effective_capacity_m3s <= 0.0:
            return 999.9 if current_flow_m3s > 0.0 else 0.0
        return round((current_flow_m3s / effective_capacity_m3s) * 100.0, 2)

    @staticmethod
    def calculate_excess_flow(current_flow_m3s: float, effective_capacity_m3s: float) -> float:
        """Calculates uncontained surface overflow volume (surcharge) in m3/s."""
        return round(max(0.0, current_flow_m3s - effective_capacity_m3s), 4)

    def build_graph(self, force_rebuild: bool = False) -> nx.DiGraph:
        """Constructs and validates the directed graph representation of the drainage network."""
        if self._graph is not None and not force_rebuild:
            return self._graph

        nodes = self.service.get_node_models()
        edges = self.service.get_edge_models()

        g = nx.DiGraph()
        node_ids: Set[str] = set()

        for node in nodes:
            g.add_node(
                node.node_id,
                name=node.name,
                latitude=node.latitude,
                longitude=node.longitude,
                elevation_m=node.elevation_m,
                type=node.type,
                associated_zone_id=node.associated_zone_id,
            )
            node_ids.add(node.node_id)

        self._edge_lookup = {}
        for edge in edges:
            if edge.from_node not in node_ids:
                raise InvalidDrainageDataFormatError(
                    f"Edge {edge.edge_id} references non-existent from_node: {edge.from_node}"
                )
            if edge.to_node not in node_ids:
                raise InvalidDrainageDataFormatError(
                    f"Edge {edge.edge_id} references non-existent to_node: {edge.to_node}"
                )

            g.add_edge(
                edge.from_node,
                edge.to_node,
                edge_id=edge.edge_id,
                street_name=edge.street_name,
                capacity_m3s=edge.capacity_m3s,
                current_flow_m3s=edge.current_flow_m3s,
                blockage_percent=edge.blockage_percent,
                length_m=edge.length_m,
            )
            self._edge_lookup[edge.edge_id.upper()] = (edge.from_node, edge.to_node)

        self._graph = g
        return g

    def evaluate_edge_metrics(
        self,
        edge_id: str,
        blockage_override: Optional[float] = None,
        flow_override: Optional[float] = None,
    ) -> DrainageEdgeMetrics:
        """Calculates hydraulic performance metrics for a specific edge."""
        g = self.build_graph()
        edge_key = edge_id.upper()
        if edge_key not in self._edge_lookup:
            raise KeyError(f"Drainage conduit ID {edge_id} not found in network")

        u, v = self._edge_lookup[edge_key]
        attr = g.edges[u, v]

        capacity = float(attr["capacity_m3s"])
        blockage = float(blockage_override if blockage_override is not None else attr["blockage_percent"])
        current_flow = float(flow_override if flow_override is not None else attr["current_flow_m3s"])
        length_m = float(attr["length_m"])
        street_name = attr.get("street_name")

        eff_cap = self.calculate_effective_capacity(capacity, blockage)
        utilization = self.calculate_utilization(current_flow, eff_cap)
        status = self.classify_drain_status(utilization)
        is_surcharged = utilization > 100.0
        excess = self.calculate_excess_flow(current_flow, eff_cap)

        # Topological traversal
        upstream = list(g.predecessors(u))
        downstream = list(g.successors(v))

        return DrainageEdgeMetrics(
            edge_id=attr["edge_id"],
            from_node=u,
            to_node=v,
            street_name=street_name,
            capacity_m3s=capacity,
            blockage_percent=blockage,
            effective_capacity_m3s=eff_cap,
            current_flow_m3s=current_flow,
            utilization_percent=utilization,
            status=status,
            is_surcharged=is_surcharged,
            excess_flow_m3s=excess,
            length_m=length_m,
            upstream_nodes=upstream,
            downstream_nodes=downstream,
        )

    def evaluate_node_metrics(
        self, node_id: str, blockage_override: Optional[float] = None
    ) -> DrainageNodeModel:
        """Calculates inflow, outflow capacity, and surcharge state for a junction node."""
        g = self.build_graph()
        if node_id not in g:
            raise KeyError(f"Drainage node ID {node_id} not found in network")

        attr = g.nodes[node_id]

        # Calculate incoming flow
        inflow = 0.0
        for u in g.predecessors(node_id):
            inflow += float(g.edges[u, node_id]["current_flow_m3s"])

        # Calculate outgoing capacity
        outflow_cap = 0.0
        node_status = DrainStatus.NORMAL
        is_surcharged = False

        out_edges = list(g.successors(node_id))
        if out_edges:
            for v in out_edges:
                e_attr = g.edges[node_id, v]
                edge_blockage = (
                    float(blockage_override)
                    if blockage_override is not None
                    else float(e_attr["blockage_percent"])
                )
                eff_cap = self.calculate_effective_capacity(
                    e_attr["capacity_m3s"], edge_blockage
                )
                outflow_cap += eff_cap
                util = self.calculate_utilization(e_attr["current_flow_m3s"], eff_cap)
                edge_status = self.classify_drain_status(util)
                if edge_status == DrainStatus.SURCHARGED:
                    is_surcharged = True
                    node_status = DrainStatus.SURCHARGED
                elif edge_status == DrainStatus.CRITICAL and node_status != DrainStatus.SURCHARGED:
                    node_status = DrainStatus.CRITICAL
                elif edge_status == DrainStatus.WARNING and node_status not in [DrainStatus.SURCHARGED, DrainStatus.CRITICAL]:
                    node_status = DrainStatus.WARNING
        else:
            # Outfall or terminal node
            outflow_cap = inflow

        if inflow > outflow_cap and outflow_cap > 0.0:
            is_surcharged = True
            node_status = DrainStatus.SURCHARGED

        return DrainageNodeModel(
            node_id=node_id,
            name=attr["name"],
            latitude=attr["latitude"],
            longitude=attr["longitude"],
            elevation_m=attr["elevation_m"],
            type=attr["type"],
            associated_zone_id=attr.get("associated_zone_id"),
            status=node_status,
            inflow_m3s=round(inflow, 4),
            outflow_capacity_m3s=round(outflow_cap, 4),
            is_surcharged=is_surcharged,
        )

    def evaluate_entire_network(
        self, blockage_override: Optional[float] = None
    ) -> DrainageNetworkResponse:
        """Executes full dynamic hydraulic evaluation across all nodes and edges."""
        dataset = self.service.load_dataset()
        g = self.build_graph()

        evaluated_edges: List[DrainageEdgeMetrics] = []
        normal_cnt = 0
        warning_cnt = 0
        critical_cnt = 0
        surcharged_cnt = 0
        total_design_cap = 0.0
        total_eff_cap = 0.0
        total_flow = 0.0
        total_excess = 0.0
        max_util = 0.0
        bottlenecks: List[str] = []

        for edge_id in self._edge_lookup:
            metrics = self.evaluate_edge_metrics(edge_id, blockage_override=blockage_override)
            evaluated_edges.append(metrics)

            total_design_cap += metrics.capacity_m3s
            total_eff_cap += metrics.effective_capacity_m3s
            total_flow += metrics.current_flow_m3s
            total_excess += metrics.excess_flow_m3s
            max_util = max(max_util, metrics.utilization_percent)

            if metrics.status == DrainStatus.NORMAL:
                normal_cnt += 1
            elif metrics.status == DrainStatus.WARNING:
                warning_cnt += 1
            elif metrics.status == DrainStatus.CRITICAL:
                critical_cnt += 1
                bottlenecks.append(metrics.edge_id)
            elif metrics.status == DrainStatus.SURCHARGED:
                surcharged_cnt += 1
                bottlenecks.append(metrics.edge_id)

        evaluated_nodes: List[DrainageNodeModel] = []
        for n in g.nodes:
            node_model = self.evaluate_node_metrics(n, blockage_override=blockage_override)
            evaluated_nodes.append(node_model)

        summary = DrainageNetworkSummary(
            total_nodes=len(evaluated_nodes),
            total_edges=len(evaluated_edges),
            normal_drains=normal_cnt,
            warning_drains=warning_cnt,
            critical_drains=critical_cnt,
            surcharged_drains=surcharged_cnt,
            max_utilization_percent=round(max_util, 2),
            total_design_capacity_m3s=round(total_design_cap, 4),
            total_effective_capacity_m3s=round(total_eff_cap, 4),
            total_flow_m3s=round(total_flow, 4),
            total_excess_flow_m3s=round(total_excess, 4),
            bottleneck_drains=bottlenecks,
        )

        return DrainageNetworkResponse(
            location=dataset.get("location", "Urban Drainage Catchment"),
            data_type=dataset.get("data_type", "DEMO-SIMULATED"),
            generated_at=dataset.get("generated_at", "2026-09-09T00:00:00Z"),
            summary=summary,
            nodes=evaluated_nodes,
            drains=evaluated_edges,
            source_note=dataset.get(
                "source_note",
                "Synthetic urban drainage network model for prototype demonstration."
            ),
            limitation_note=dataset.get(
                "limitation_note",
                "Prototype capacity-based surcharge model; not a complete 2D hydrodynamic simulation."
            ),
        )


# Global singleton instance
default_drainage_engine = DrainageEngine()
