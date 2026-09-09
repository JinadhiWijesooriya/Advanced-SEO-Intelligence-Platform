"""
Notifications API Endpoints - Phase 9
Allows users to view and manage their in-app notifications.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import Notification as NotificationSchema

router = APIRouter()


@router.get(
    "/notifications",
    response_model=List[NotificationSchema],
    summary="List user notifications",
    tags=["Notifications"],
)
def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve notifications for the authenticated user.
    Optionally filter to unread-only. Returns up to limit entries, newest first.
    """
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.read_at == None)
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return notifications


@router.get(
    "/notifications/unread-count",
    summary="Get unread notification count",
    tags=["Notifications"],
)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the count of unread notifications for the current user."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.read_at == None)
        .count()
    )
    return {"unread_count": count}


@router.put(
    "/notifications/{notification_id}/read",
    response_model=NotificationSchema,
    summary="Mark a notification as read",
    tags=["Notifications"],
)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a specific notification as read by setting read_at timestamp."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    if notif.read_at is None:
        notif.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notif)
    return notif


@router.put(
    "/notifications/read-all",
    summary="Mark all notifications as read",
    tags=["Notifications"],
)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all unread notifications for the current user as read."""
    now = datetime.now(timezone.utc)
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.read_at == None)
        .update({"read_at": now})
    )
    db.commit()
    return {"marked_read": updated}


@router.delete(
    "/notifications/{notification_id}",
    status_code=204,
    summary="Delete a notification",
    tags=["Notifications"],
)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific notification."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    db.delete(notif)
    db.commit()
