"""Profile API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request

from app.services.profile_service import ProfileService


router = APIRouter(prefix="/api/profile", tags=["profile"])


def get_profile_service(request: Request) -> ProfileService:
    return request.app.state.profile_service


@router.get("/me")
async def get_my_profile(
    user_id: int = 1,
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Get current user's profile."""
    result = profile_service.get_profile(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.get("/{user_id}")
async def get_user_profile(
    user_id: int,
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Get a user's profile by ID."""
    result = profile_service.get_profile(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.get("/me/versions")
async def get_profile_versions(
    user_id: int = 1,
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Get profile version history."""
    return profile_service.get_versions(user_id)


@router.get("/me/versions/{version}")
async def get_profile_version(
    version: int,
    user_id: int = 1,
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Get a specific profile version snapshot."""
    result = profile_service.get_version(user_id, version)
    if not result:
        raise HTTPException(status_code=404, detail="Version not found")
    return result


@router.post("/me/export")
async def export_profile(
    user_id: int = 1,
    profile_service: ProfileService = Depends(get_profile_service),
):
    """GDPR-compliant data export."""
    result = profile_service.export_profile(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.delete("/me")
async def delete_profile(
    user_id: int = 1,
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Delete profile data (GDPR right to be forgotten)."""
    return profile_service.delete_profile(user_id)
