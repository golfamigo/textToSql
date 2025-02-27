"""
測試模型錯誤驗證
"""
import pytest
import uuid
from datetime import datetime, time, date, timedelta
from pydantic import ValidationError

from app.models.users import UserModel, UserRole
from app.models.bookings import BookingModel, BookingStatus
from app.models.services import ServiceModel
from app.models.time_periods import TimePeriodModel, WeekDay
from app.models.query_history import QueryHistoryModel, QueryTemplateModel


class TestUserModelErrors:
    """測試 UserModel 錯誤驗證"""

    def test_invalid_email_format(self):
        """測試無效的電子郵件格式"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        invalid_email = "invalid-email"  # 無效的電子郵件格式

        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            UserModel(
                id=test_id,
                business_id=business_id,
                email=invalid_email,
                name="測試用戶",
                role=UserRole.STAFF
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("email" in str(err).lower() for err in error_details)

    def test_invalid_role_value(self):
        """測試無效的用戶角色"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            UserModel(
                id=test_id,
                business_id=business_id,
                email="test@example.com",
                name="測試用戶",
                role="invalid_role"  # 無效的角色值
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("role" in str(err).lower() for err in error_details)

    def test_missing_required_fields(self):
        """測試缺少必填欄位"""
        # 準備測試數據
        test_id = uuid.uuid4()
        
        # 驗證是否引發 ValidationError (缺少 business_id)
        with pytest.raises(ValidationError) as exc_info:
            UserModel(
                id=test_id,
                email="test@example.com",
                name="測試用戶",
                role=UserRole.CUSTOMER
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("business_id" in str(err).lower() for err in error_details)


class TestBookingModelErrors:
    """測試 BookingModel 錯誤驗證"""

    def test_end_time_before_start_time(self):
        """測試結束時間在開始時間之前的錯誤"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        customer_id = uuid.uuid4()
        service_id = uuid.uuid4()
        period_id = uuid.uuid4()
        start_time = datetime(2025, 2, 15, 10, 0)
        end_time = datetime(2025, 2, 15, 9, 0)  # 結束時間在開始時間之前
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            BookingModel(
                id=test_id,
                business_id=business_id,
                customer_id=customer_id,
                service_id=service_id,
                period_id=period_id,
                start_time=start_time,
                end_time=end_time,
                status=BookingStatus.PENDING
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("結束時間必須晚於開始時間" in str(err) for err in error_details)
    
    def test_invalid_booking_status(self):
        """測試無效的預約狀態"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        customer_id = uuid.uuid4()
        service_id = uuid.uuid4()
        period_id = uuid.uuid4()
        start_time = datetime(2025, 2, 15, 10, 0)
        end_time = datetime(2025, 2, 15, 11, 0)
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            BookingModel(
                id=test_id,
                business_id=business_id,
                customer_id=customer_id,
                service_id=service_id,
                period_id=period_id,
                start_time=start_time,
                end_time=end_time,
                status="invalid_status"  # 無效的預約狀態
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("status" in str(err).lower() for err in error_details)


class TestServiceModelErrors:
    """測試 ServiceModel 錯誤驗證"""

    def test_negative_price(self):
        """測試負數價格"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ServiceModel(
                id=test_id,
                business_id=business_id,
                name="測試服務",
                duration=timedelta(hours=1),
                price=-100  # 負數價格
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("price" in str(err).lower() for err in error_details)
    
    def test_zero_duration(self):
        """測試零時長"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ServiceModel(
                id=test_id,
                business_id=business_id,
                name="測試服務",
                duration=timedelta(seconds=0),  # 零時長
                price=100
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("duration" in str(err).lower() for err in error_details)


class TestTimePeriodModelErrors:
    """測試 TimePeriodModel 錯誤驗證"""

    def test_end_time_before_start_time(self):
        """測試結束時間在開始時間之前的錯誤"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        start_time = time(10, 0)
        end_time = time(9, 0)  # 結束時間在開始時間之前
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            TimePeriodModel(
                id=test_id,
                business_id=business_id,
                start_time=start_time,
                end_time=end_time,
                day_of_week=WeekDay.MONDAY
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("結束時間必須晚於開始時間" in str(err) for err in error_details)
    
    def test_missing_date_specification(self):
        """測試缺少日期指定（星期幾或特定日期）"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            TimePeriodModel(
                id=test_id,
                business_id=business_id,
                start_time=time(9, 0),
                end_time=time(17, 0),
                # 未指定 day_of_week 或 specific_date
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("必須指定 day_of_week 或 specific_date" in str(err) for err in error_details)

    def test_invalid_day_of_week(self):
        """測試無效的星期幾值"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            TimePeriodModel(
                id=test_id,
                business_id=business_id,
                start_time=time(9, 0),
                end_time=time(17, 0),
                day_of_week=8  # 無效的星期幾 (只允許 1-7)
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("day_of_week" in str(err).lower() for err in error_details)


class TestQueryHistoryModelErrors:
    """測試 QueryHistoryModel 錯誤驗證"""

    def test_negative_execution_time(self):
        """測試負數執行時間"""
        # 準備測試數據
        
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            QueryHistoryModel(
                user_query="列出所有活躍的商家",
                generated_sql="SELECT * FROM n8n_booking_businesses WHERE is_active = true;",
                executed=True,
                execution_time=-1.5  # 負數執行時間
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("execution_time" in str(err).lower() for err in error_details)

    def test_missing_required_fields(self):
        """測試缺少必填欄位"""
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            QueryHistoryModel(
                # 缺少 user_query
                generated_sql="SELECT * FROM n8n_booking_businesses WHERE is_active = true;"
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("user_query" in str(err).lower() for err in error_details)


class TestQueryTemplateModelErrors:
    """測試 QueryTemplateModel 錯誤驗證"""

    def test_empty_name(self):
        """測試空名稱"""
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            QueryTemplateModel(
                name="",  # 空名稱
                description="測試模板",
                user_query="列出所有活躍的商家",
                generated_sql="SELECT * FROM n8n_booking_businesses WHERE is_active = true;"
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("name" in str(err).lower() for err in error_details)

    def test_invalid_tags_format(self):
        """測試無效的標籤格式"""
        # 驗證是否引發 ValidationError
        with pytest.raises(ValidationError) as exc_info:
            QueryTemplateModel(
                name="測試模板",
                description="測試模板描述",
                user_query="列出所有活躍的商家",
                generated_sql="SELECT * FROM n8n_booking_businesses WHERE is_active = true;",
                tags="商家,基礎查詢"  # 無效格式 (應為列表)
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("tags" in str(err).lower() for err in error_details)