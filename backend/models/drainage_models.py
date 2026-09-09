"""Pydantic models for drainage network nodes, pipes/edges, utilization, and surcharge conditions."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DrainStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    SURCHARGED = "SURCHARGED"


class DrainageNodeModel(BaseModel):
    """Represents a drainage network junction, manhole, inlet, or outfall."""
    node_id: str = Field(..., description="Unique node identifier (e.g. N01)")
    name: str = Field(..., description="Descriptive name of the drainage node")
    latitude: float = Field(..., description="Geographic latitude")
    longitude: float = Field(..., description="Geographic longitude")
    elevation_m: float = Field(..., description="Invert/surface elevation in meters")
    type: str = Field(..., description="Node classification: inlet, manhole, junction, or outfall")
    associated_zone_id: Optional[str] = Field(None, description="Linked surface catchment zone ID if applicable")
    status: DrainStatus = Field(default=DrainStatus.NORMAL, description="Calculated operating status of the node")
    inflow_m3s: float = Field(default=0.0, ge=0.0, description="Total inflow arriving at this node in m3/s")
    outflow_capacity_m3s: float = Field(default=0.0, ge=0.0, description="Total downstream effective discharge capacity in m3/s")
    is_surcharged: bool = Field(default=False, description="Flag indicating if arriving flow exceeds outflow capacity")


class DrainageEdgeModel(BaseModel):
    """Input definition for a directed pipe, conduit, or drainage channel."""
    edge_id: str = Field(..., description="Unique edge identifier (e.g. E01)")
    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Destination node ID")
    street_name: Optional[str] = Field(None, description="Associated street corridor name")
    capacity_m3s: float = Field(..., ge=0.0, description="Original design conduit hydraulic capacity in m3/s")
    current_flow_m3s: float = Field(..., ge=0.0, description="Observed or simulated discharge flow rate in m3/s")
    blockage_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Pipe siltation or obstruction percentage (0-100%)")
    length_m: float = Field(..., gt=0.0, description="Physical conduit length in meters")


class DrainageEdgeMetrics(BaseModel):
    """Evaluated hydraulic performance metrics for a drainage conduit."""
    edge_id: str = Field(..., description="Conduit identifier")
    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Destination node ID")
    street_name: Optional[str] = Field(None, description="Associated street corridor name")
    capacity_m3s: float = Field(..., ge=0.0, description="Physical design capacity in m3/s")
    blockage_percent: float = Field(..., ge=0.0, le=100.0, description="Blockage percentage")
    effective_capacity_m3s: float = Field(..., ge=0.0, description="Effective capacity accounting for blockage in m3/s")
    current_flow_m3s: float = Field(..., ge=0.0, description="Current flow rate in m3/s")
    utilization_percent: float = Field(..., ge=0.0, description="Conduit flow capacity utilization percentage")
    status: DrainStatus = Field(..., description="Operating status (NORMAL, WARNING, CRITICAL, SURCHARGED)")
    is_surcharged: bool = Field(..., description="True if utilization > 100%")
    excess_flow_m3s: float = Field(..., ge=0.0, description="Excess uncontained flow volume exceeding effective capacity")
    length_m: float = Field(..., gt=0.0, description="Length in meters")
    upstream_nodes: List[str] = Field(default_factory=list, description="Immediate upstream feeder node IDs")
    downstream_nodes: List[str] = Field(default_factory=list, description="Immediate downstream recipient node IDs")


class DrainageNetworkSummary(BaseModel):
    """Aggregated operational summary of the urban drainage network."""
    total_nodes: int = Field(..., description="Total count of nodes in the network")
    total_edges: int = Field(..., description="Total count of conduit edges in the network")
    normal_drains: int = Field(..., description="Number of drains operating at < 70% utilization")
    warning_drains: int = Field(..., description="Number of drains operating at 70% - 90% utilization")
    critical_drains: int = Field(..., description="Number of drains operating at 90% - 100% utilization")
    surcharged_drains: int = Field(..., description="Number of drains operating at > 100% utilization")
    max_utilization_percent: float = Field(..., description="Highest conduit utilization percentage in the network")
    total_design_capacity_m3s: float = Field(..., description="Summed original physical design capacity in m3/s")
    total_effective_capacity_m3s: float = Field(..., description="Summed available effective capacity after blockage in m3/s")
    total_flow_m3s: float = Field(..., description="Total aggregate flow entering conduits in m3/s")
    total_excess_flow_m3s: float = Field(..., description="Total uncontained surface surcharge flow in m3/s")
    bottleneck_drains: List[str] = Field(default_factory=list, description="List of conduit IDs operating above capacity")


class DrainageNetworkResponse(BaseModel):
    """Full API response schema for drainage network intelligence."""
    location: str = Field(..., description="Target urban catchment location")
    data_type: str = Field(default="DEMO-SIMULATED", description="Data provenance classification")
    generated_at: str = Field(..., description="Simulation timestamp")
    summary: DrainageNetworkSummary = Field(..., description="Aggregated network operational summary")
    nodes: List[DrainageNodeModel] = Field(..., description="Drainage nodes with calculated surcharge states")
    drains: List[DrainageEdgeMetrics] = Field(..., description="Drainage conduits with evaluated hydraulic metrics")
    source_note: str = Field(
        default="Synthetic urban drainage network model for prototype demonstration. Not municipal utility survey data.",
        description="Data provenance statement"
    )
    limitation_note: str = Field(
        default="Prototype drainage-capacity model. Surcharge is evaluated via flow vs. effective capacity thresholding; not a complete 2D hydrodynamic backflow simulation.",
        description="Methodological limitations disclosure"
    )
