from typing import Optional

from models.church_activity import ChurchActivity



class ChurchActivityRepository:
    def __init__(self, connection):
        self.connection = connection

    def create(self, activity: ChurchActivity) -> ChurchActivity:
        cursor = self.connection.execute(
            "INSERT INTO church_activities (tenant_id, name, description, activity_type, purpose, program_id, status, delivery_mode, scheduled_start, scheduled_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (activity.tenant_id, activity.name, activity.description, activity.activity_type, activity.purpose, activity.program_id, activity.status.value, activity.delivery_mode.value, activity.scheduled_start, activity.scheduled_end),
        )
        self.connection.commit()
        return ChurchActivity(id=cursor.lastrowid, tenant_id=activity.tenant_id, name=activity.name, description=activity.description, activity_type=activity.activity_type, purpose=activity.purpose, program_id=activity.program_id, status=activity.status, delivery_mode=activity.delivery_mode, scheduled_start=activity.scheduled_start, scheduled_end=activity.scheduled_end, created_at=activity.created_at)

    def get(self, tenant_id: str, activity_id: int) -> Optional[ChurchActivity]:
        row = self.connection.execute(
            "SELECT id, tenant_id, name, description, activity_type, purpose, program_id, status, delivery_mode, scheduled_start, scheduled_end, created_at FROM church_activities WHERE tenant_id = ? AND id = ?",
            (tenant_id, activity_id),
        ).fetchone()
        if row is None:
            return None
        return self._to_model(row)

    def list(self, tenant_id: str) -> list[ChurchActivity]:
        rows = self.connection.execute(
            "SELECT id, tenant_id, name, description, activity_type, purpose, program_id, status, delivery_mode, scheduled_start, scheduled_end, created_at FROM church_activities WHERE tenant_id = ? ORDER BY id",
            (tenant_id,),
        ).fetchall()
        return [self._to_model(row) for row in rows]

    @staticmethod
    def _to_model(row) -> ChurchActivity:
        from models.church_activity import ChurchActivityDeliveryMode, ChurchActivityStatus
        return ChurchActivity(id=row["id"], tenant_id=row["tenant_id"], name=row["name"], description=row["description"], activity_type=row["activity_type"], purpose=row["purpose"], program_id=row["program_id"], status=ChurchActivityStatus(row["status"]), delivery_mode=ChurchActivityDeliveryMode(row["delivery_mode"]), scheduled_start=row["scheduled_start"], scheduled_end=row["scheduled_end"], created_at=row["created_at"])
