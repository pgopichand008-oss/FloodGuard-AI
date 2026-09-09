"""API endpoints for urban drainage network intelligence, utilization, and surcharge modeling."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.engines.drainage_engine import (
    DrainageEngine,
    default_drainage_engine,
)
from backend.models.drainage_models import (
    DrainStatus,
    DrainageNetworkResponse,
)
from backend.services.drainage_service import (
    DrainageFileNotFoundError,
    DrainageServiceError,
    InvalidDrainageDataFormatError,
)

router = APIRouter(tags=["Drainage Network Intelligence"])


@router.get(
    "/drainage",
    response_model=DrainageNetworkResponse,
    summary="Get drainage network topology, hydraulic utilization, and surcharge conditions",
    description="Evaluates directed urban drainage conduits, calculates effective capacity after blockage, determines utilization and surcharge status, and returns a network operational summary.",
)
def get_drainage_network(
    node_id: Optional[str] = Query(
        default=None,
        description="Filter network around a specific drainage node ID (e.g. N02)"
    ),
    edge_id: Optional[str] = Query(
        default=None,
        description="Filter network for a single conduit ID (e.g. E03)"
    ),
    status_filter: Optional[DrainStatus] = Query(
        default=None,
        description="Filter conduits by operational status: NORMAL, WARNING, CRITICAL, or SURCHARGED"
    ),
):
    """Retrieve full or filtered urban drainage network metrics and surcharge assessment."""
    try:
        response = default_drainage_engine.evaluate_entire_network()

        # Apply filtering if requested
        if node_id:
            target_node = node_id.strip().upper()
            filtered_nodes = [n for n in response.nodes if n.node_id.upper() == target_node]
            if not filtered_nodes:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Drainage node {node_id} not found in network"
                )
            response.nodes = filtered_nodes
            response.drains = [
                d for d in response.drains
                if d.from_node.upper() == target_node or d.to_node.upper() == target_node
            ]

        if edge_id:
            target_edge = edge_id.strip().upper()
            filtered_drains = [d for d in response.drains if d.edge_id.upper() == target_edge]
            if not filtered_drains:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Drainage edge {edge_id} not found in network"
                )
            response.drains = filtered_drains

        if status_filter:
            response.drains = [d for d in response.drains if d.status == status_filter]

        return response

    except HTTPException:
        raise
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )
    except DrainageFileNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drainage dataset not found: {err}"
        )
    except (InvalidDrainageDataFormatError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid drainage data specification: {err}"
        )
    except DrainageServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error evaluating drainage network: {err}"
        )
