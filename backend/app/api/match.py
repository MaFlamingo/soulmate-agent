"""Match API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas.match import (
    MatchRequest, MatchFeedbackRequest, IceBreakerRequest,
)
from app.services.matching_service import MatchingService


router = APIRouter(prefix="/api/match", tags=["match"])


def get_matching_service(request: Request) -> MatchingService:
    return request.app.state.matching_service


@router.post("/request")
async def request_match(
    body: MatchRequest = MatchRequest(user_id=1, k=5),
    matching_service: MatchingService = Depends(get_matching_service),
):
    """Trigger a matching run for the user."""
    result = await matching_service.request_match(body.user_id, k=body.k)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/results")
async def get_match_results(
    user_id: int = 1,
    limit: int = 20,
    offset: int = 0,
    matching_service: MatchingService = Depends(get_matching_service),
):
    """Get user's match results."""
    return matching_service.get_results(user_id, limit=limit, offset=offset)


@router.get("/{match_id}")
async def get_match_detail(
    match_id: int,
    matching_service: MatchingService = Depends(get_matching_service),
):
    """Get detailed match info with explanation and icebreakers."""
    result = await matching_service.get_match_detail(match_id)
    if not result:
        raise HTTPException(status_code=404, detail="Match not found")
    return result


@router.post("/{match_id}/feedback")
async def submit_feedback(
    match_id: int,
    body: MatchFeedbackRequest,
    matching_service: MatchingService = Depends(get_matching_service),
):
    """Submit feedback on a match."""
    result = matching_service.submit_feedback(
        match_id, accepted=body.accepted, feedback_text=body.feedback_text,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{match_id}/icebreaker")
async def generate_icebreaker(
    match_id: int,
    matching_service: MatchingService = Depends(get_matching_service),
):
    """Generate icebreaker messages (3 styles) for a match."""
    result = await matching_service.generate_icebreakers(match_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{match_id}/icebreakers")
async def get_icebreakers(
    match_id: int,
    matching_service: MatchingService = Depends(get_matching_service),
):
    """Get all icebreaker messages for a match."""
    return matching_service.get_icebreakers(match_id)
