"""
Settings API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_database
from app.models.user_settings import UserSettings
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_database)
):
    """Get user settings."""
    result = await db.execute(select(UserSettings).where(UserSettings.id == 1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings
        settings = UserSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return UserSettingsResponse(
        default_job_titles=settings.default_job_titles,
        default_domains=settings.default_domains,
        max_yoe=settings.max_yoe,
        preferred_locations=settings.preferred_locations,
        remote_only=settings.remote_only,
        excluded_keywords=settings.excluded_keywords,
        cloud_storage_config=settings.cloud_storage_config
    )


@router.put("", response_model=UserSettingsResponse)
async def update_settings(
    settings_update: UserSettingsUpdate,
    db: AsyncSession = Depends(get_database)
):
    """Update user settings."""
    result = await db.execute(select(UserSettings).where(UserSettings.id == 1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserSettings(id=1)
        db.add(settings)
    
    # Update fields
    update_data = settings_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    
    return UserSettingsResponse(
        default_job_titles=settings.default_job_titles,
        default_domains=settings.default_domains,
        max_yoe=settings.max_yoe,
        preferred_locations=settings.preferred_locations,
        remote_only=settings.remote_only,
        excluded_keywords=settings.excluded_keywords,
        cloud_storage_config=settings.cloud_storage_config
    )
