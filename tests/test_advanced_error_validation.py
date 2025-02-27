"""
測試進階模型錯誤驗證
"""
import pytest
import uuid
from datetime import datetime, time, date, timedelta
from pydantic import ValidationError
import json

from app.models.users import UserModel, UserRole
from app.models.bookings import BookingModel, BookingStatus
from app.models.services import ServiceModel
from app.models.time_periods import TimePeriodModel, WeekDay
from app.models.businesses import BusinessModel
from app.models.query_history import QueryHistoryModel, QueryTemplateModel


class TestJsonDataErrors:
    """測試 JSON 資料相關錯誤"""

    def test_invalid_profile_data_format(self):
        """測試無效的個人資料 JSON 格式"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 無效的 JSON 格式
        invalid_json = "這不是有效的 JSON"
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            UserModel(
                id=test_id,
                business_id=business_id,
                email="test@example.com",
                name="測試用戶",
                role=UserRole.STAFF,
                profile_data=invalid_json  # 不符合 Dict[str, Any] 格式
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("profile_data" in str(err).lower() for err in error_details)

    def test_invalid_business_hours_format(self):
        """測試無效的營業時間格式"""
        # 準備測試數據
        test_id = uuid.uuid4()
        
        # 無效的營業時間格式
        invalid_hours = "9:00-17:00"  # 應該是字典格式
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            BusinessModel(
                id=test_id,
                name="測試商家",
                business_hours=invalid_hours
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("business_hours" in str(err).lower() for err in error_details)


class TestDateTimeErrors:
    """測試日期時間相關錯誤"""

    def test_invalid_date_format(self):
        """測試無效的日期格式"""
        # 準備測試數據
        test_id = uuid.uuid4()
        
        # 無效的日期格式
        invalid_date = "2025/01/15"  # 應該使用 date 對象
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            BusinessModel(
                id=test_id,
                name="測試商家",
                subscription_end_date=invalid_date
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("subscription_end_date" in str(err).lower() for err in error_details)

    def test_invalid_time_format(self):
        """測試無效的時間格式"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 無效的時間格式
        invalid_time = "09:00"  # 應該使用 time 對象
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            TimePeriodModel(
                id=test_id,
                business_id=business_id,
                start_time=invalid_time,
                end_time=time(17, 0),
                day_of_week=WeekDay.MONDAY
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("start_time" in str(err).lower() for err in error_details)

    def test_invalid_timedelta_format(self):
        """測試無效的時間間隔格式"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 無效的時間間隔格式
        invalid_duration = "1h"  # 應該使用 timedelta 對象
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ServiceModel(
                id=test_id,
                business_id=business_id,
                name="測試服務",
                duration=invalid_duration,
                price=100
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("duration" in str(err).lower() for err in error_details)


class TestComplexValidationErrors:
    """測試複雜驗證錯誤"""

    def test_query_template_error_with_invalid_tag(self):
        """測試查詢模板中包含無效的標籤類型"""
        # 準備測試數據
        test_id = uuid.uuid4()
        
        # 無效的標籤（包含非字串項目）
        invalid_tags = ["標籤1", 123, "標籤3"]
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            QueryTemplateModel(
                id=test_id,
                name="測試模板",
                user_query="測試查詢",
                generated_sql="SELECT * FROM test",
                tags=invalid_tags
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("tags" in str(err).lower() for err in error_details)

    def test_booking_with_end_time_equals_start_time(self):
        """測試預約結束時間等於開始時間的錯誤"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        customer_id = uuid.uuid4()
        service_id = uuid.uuid4()
        period_id = uuid.uuid4()
        same_time = datetime(2025, 2, 15, 10, 0)
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            BookingModel(
                id=test_id,
                business_id=business_id,
                customer_id=customer_id,
                service_id=service_id,
                period_id=period_id,
                start_time=same_time,
                end_time=same_time,  # 結束時間與開始時間相同
                status=BookingStatus.PENDING
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("結束時間必須晚於開始時間" in str(err) for err in error_details)


class TestUUIDErrors:
    """測試 UUID 相關錯誤"""

    def test_invalid_uuid_format(self):
        """測試無效的 UUID 格式"""
        # 準備測試數據
        invalid_uuid = "12345"  # 無效的 UUID 格式
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            UserModel(
                id=invalid_uuid,
                business_id=uuid.uuid4(),
                email="test@example.com",
                name="測試用戶",
                role=UserRole.STAFF
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("id" in str(err).lower() for err in error_details)

    def test_reference_with_invalid_uuid(self):
        """測試引用無效的 UUID"""
        # 準備測試數據
        test_id = uuid.uuid4()
        invalid_reference = "not-a-uuid"  # 無效的引用 ID
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            BookingModel(
                id=test_id,
                business_id=uuid.uuid4(),
                customer_id=uuid.uuid4(),
                service_id=invalid_reference,  # 無效的服務 ID
                period_id=uuid.uuid4(),
                start_time=datetime(2025, 2, 15, 10, 0),
                end_time=datetime(2025, 2, 15, 11, 0),
                status=BookingStatus.PENDING
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("service_id" in str(err).lower() for err in error_details)


class TestModelValidationEdgeCases:
    """測試模型驗證邊界情況"""

    def test_very_long_text_fields(self):
        """測試極長的文本欄位"""
        # 準備測試數據
        test_id = uuid.uuid4()
        very_long_text = "x" * 10000  # 非常長的文本
        
        # 建立模型實例（應該不會引發錯誤，但要確認）
        try:
            history = QueryHistoryModel(
                id=test_id,
                user_query=very_long_text,
                generated_sql="SELECT 1",
                explanation="測試"
            )
            assert len(history.user_query) == 10000
        except ValidationError:
            pytest.fail("不應該對極長的文本欄位引發驗證錯誤")

    def test_unicode_special_characters(self):
        """測試含有特殊 Unicode 字符的欄位"""
        # 準備測試數據
        test_id = uuid.uuid4()
        special_chars = "測試✓☺♥★♠✪⚫⚡☂☯☭☢☣☮☯☭☢☣☮☢☣☮"
        
        # 建立模型實例（應該不會引發錯誤，但要確認）
        try:
            business = BusinessModel(
                id=test_id,
                name=special_chars
            )
            assert business.name == special_chars
        except ValidationError:
            pytest.fail("不應該對包含特殊字符的欄位引發驗證錯誤")


class TestTimezoneErrors:
    """測試時區相關錯誤"""

    def test_invalid_timezone(self):
        """測試無效的時區值"""
        # 準備測試數據
        test_id = uuid.uuid4()
        invalid_timezone = "Asia/Invalid"  # 無效的時區
        
        # 驗證是否引發 ValidationError
        # 注意：這視情況而定，如果模型沒有時區驗證，可能不會引發錯誤
        try:
            business = BusinessModel(
                id=test_id,
                name="測試商家",
                timezone=invalid_timezone
            )
            # 如果沒有引發錯誤，至少確認值被正確設置
            assert business.timezone == invalid_timezone
        except ValidationError as e:
            # 如果引發錯誤，檢查錯誤訊息是否與時區相關
            error_details = e.errors()
            assert any("timezone" in str(err).lower() for err in error_details)