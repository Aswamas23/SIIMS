from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.system_settings import SystemSetting
from app.models.users import User
from app.schemas.settings import SettingResponse, BatchSettingUpdate, EmailTestResponse
from app.utils.helpers import log_audit
from app.utils.email import send_email_from_db_settings
from app.core.config import settings as app_settings

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/", response_model=list[SettingResponse])
async def list_settings(
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all system settings (admin only)."""
    result = await db.execute(
        select(SystemSetting).order_by(SystemSetting.category, SystemSetting.key)
    )
    return result.scalars().all()


@router.put("/", response_model=list[SettingResponse])
async def update_settings(
    request: Request,
    batch_data: BatchSettingUpdate,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Batch update system settings (admin only)."""
    updated_keys = []
    for update in batch_data.settings:
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == update.key)
        )
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = update.value
        else:
            setting = SystemSetting(key=update.key, value=update.value)
            db.add(setting)
        updated_keys.append(update.key)

    await log_audit(
        db,
        action="update_settings",
        user_id=current_user.id,
        entity_type="system_settings",
        details={"keys_updated": updated_keys},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key.in_(updated_keys))
    )
    return result.scalars().all()


@router.get("/email-test", response_model=EmailTestResponse)
async def test_email(
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Send a test email to the admin's address using the configured SMTP settings."""
    success = await send_email_from_db_settings(
        db=db,
        to=current_user.email,
        subject="SIIMS — Test Email",
        body="This is a test email from SIIMS. If you received this, email notifications are working correctly.",
    )

    if success:
        return EmailTestResponse(success=True, message="Test email sent successfully")
    else:
        return EmailTestResponse(success=False, message="Failed to send test email. Check SMTP settings.")
