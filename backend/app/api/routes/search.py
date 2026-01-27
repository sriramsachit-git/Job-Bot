"""
Search API routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.api.deps import get_database
from app.services.search_service import SearchService
from app.schemas.search import SearchStart, SearchStatus, SearchResults

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/start", response_model=dict)
async def start_search(
    search_data: SearchStart,
    db: AsyncSession = Depends(get_database)
):
    """Start a new job search."""
    service = SearchService()
    search_id = await service.start_search(db, search_data)
    return {"search_id": search_id, "status": "started"}


@router.get("/{search_id}/status", response_model=SearchStatus)
async def get_search_status(
    search_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get search status."""
    service = SearchService()
    status = await service.get_search_status(db, search_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Search not found")
    
    return status


@router.get("/{search_id}/results", response_model=SearchResults)
async def get_search_results(
    search_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get search results."""
    service = SearchService()
    results = await service.get_search_results(db, search_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="Search not found")
    
    return results


@router.post("/cancel/{search_id}")
async def cancel_search(
    search_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Cancel a running search."""
    service = SearchService()
    success = await service.cancel_search(db, search_id)
    return {"status": "cancelled" if success else "failed"}


@router.websocket("/ws/{search_id}")
async def search_progress_websocket(websocket: WebSocket, search_id: int):
    """WebSocket endpoint for real-time search progress."""
    await websocket.accept()
    
    from app.database import AsyncSessionLocal
    from app.services.search_service import SearchService
    import asyncio
    
    service = SearchService()
    last_status = None
    
    try:
        while True:
            async with AsyncSessionLocal() as db:
                status = await service.get_search_status(db, search_id)
                
                if status:
                    # Only send if status changed
                    if last_status is None or status.dict() != last_status.dict():
                        await websocket.send_json(status.dict())
                        last_status = status
                    
                    # Close connection if search is done
                    if status.status in ["completed", "failed", "cancelled"]:
                        await websocket.close()
                        break
                
                # Wait before next update
                await asyncio.sleep(1)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
