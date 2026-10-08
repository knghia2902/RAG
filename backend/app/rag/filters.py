from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ScopeCriteria:
    """Tiêu chí phạm vi lọc truy xuất tri thức (RAG-03, AUTH-04)."""
    allowed_dataset_ids: set[UUID]
    target_dataset_ids: set[UUID] | None = None
    profile_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def effective_dataset_ids(self) -> set[UUID]:
        if not self.target_dataset_ids:
            return self.allowed_dataset_ids

        # Tính giao điểm nghiêm ngặt giữa quyền được cấp và phạm vi yêu cầu
        intersection = self.allowed_dataset_ids & self.target_dataset_ids
        if not intersection:
            raise PermissionError("Không có quyền truy cập vào bất kỳ Dataset nào trong phạm vi yêu cầu.")
        return intersection


class ScopeFilterBuilder:
    """Builder tạo tiêu chí lọc phạm vi và kiểm tra quyền nghiêm ngặt (AUTH-04)."""

    @staticmethod
    def build_filters(
        allowed_dataset_ids: set[UUID],
        target_dataset_ids: set[UUID] | None = None,
        profile_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> ScopeCriteria:
        criteria = ScopeCriteria(
            allowed_dataset_ids=allowed_dataset_ids,
            target_dataset_ids=target_dataset_ids,
            profile_id=profile_id,
            start_time=start_time,
            end_time=end_time,
        )
        # Kiểm tra tính hợp lệ của quyền (ném PermissionError nếu không hợp lệ)
        _ = criteria.effective_dataset_ids
        return criteria

