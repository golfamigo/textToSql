"""
測試模型邊界值驗證
"""
import pytest
import uuid
from datetime import datetime, time, date, timedelta
from pydantic import ValidationError
import sys

from app.models.users import UserModel, UserRole
from app.models.bookings import BookingModel, BookingStatus
from app.models.services import ServiceModel
from app.models.time_periods import TimePeriodModel, WeekDay
from app.models.businesses import BusinessModel
from app.models.query_history import QueryHistoryModel, QueryTemplateModel


class TestBoundaryValues:
    """測試邊界值情況"""

    def test_min_max_price_values(self):
        """測試價格的最大最小值"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 最大值測試
        max_price = sys.float_info.max
        try:
            service = ServiceModel(
                id=test_id,
                business_id=business_id,
                name="測試服務",
                duration=timedelta(hours=1),
                price=max_price
            )
            assert service.price == max_price
        except ValidationError:
            pytest.fail("不應該對最大浮點數價格引發驗證錯誤")
        
        # 零價格測試
        zero_price = 0.0
        try:
            service = ServiceModel(
                id=test_id,
                business_id=business_id,
                name="免費服務",
                duration=timedelta(hours=1),
                price=zero_price
            )
            assert service.price == zero_price
        except ValidationError:
            pytest.fail("不應該對零價格引發驗證錯誤")

    def test_extremely_short_long_durations(self):
        """測試極短和極長的時間間隔"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 極短時間測試 (1秒)
        min_duration = timedelta(seconds=1)
        try:
            service = ServiceModel(
                id=test_id,
                business_id=business_id,
                name="超短服務",
                duration=min_duration,
                price=100
            )
            assert service.duration == min_duration
        except ValidationError:
            pytest.fail("不應該對極短時間間隔引發驗證錯誤")
        
        # 極長時間測試 (1年)
        max_duration = timedelta(days=365)
        try:
            service = ServiceModel(
                id=test_id,
                business_id=business_id,
                name="超長服務",
                duration=max_duration,
                price=100
            )
            assert service.duration == max_duration
        except ValidationError:
            pytest.fail("不應該對極長時間間隔引發驗證錯誤")

    def test_time_period_boundaries(self):
        """測試時段邊界值"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 測試 23:59 到 00:01 的時段 (跨日)
        late_start = time(23, 59)
        early_end = time(0, 1)
        
        # 這應該引發錯誤，因為在時間對象比較中 00:01 < 23:59
        with pytest.raises(ValidationError) as exc_info:
            TimePeriodModel(
                id=test_id,
                business_id=business_id,
                start_time=late_start,
                end_time=early_end,
                day_of_week=WeekDay.MONDAY
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("結束時間必須晚於開始時間" in str(err) for err in error_details)
        
        # 測試 00:00 到 23:59 的時段 (整天)
        day_start = time(0, 0)
        day_end = time(23, 59)
        
        try:
            period = TimePeriodModel(
                id=test_id,
                business_id=business_id,
                start_time=day_start,
                end_time=day_end,
                day_of_week=WeekDay.MONDAY
            )
            assert period.start_time == day_start
            assert period.end_time == day_end
        except ValidationError:
            pytest.fail("不應該對整天時段引發驗證錯誤")

    def test_enum_edge_cases(self):
        """測試枚舉的邊界情況"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 測試星期幾的最小值和最大值
        min_day = WeekDay.MONDAY  # 1
        max_day = WeekDay.SUNDAY  # 7
        
        # 最小值測試
        try:
            period = TimePeriodModel(
                id=test_id,
                business_id=business_id,
                start_time=time(9, 0),
                end_time=time(17, 0),
                day_of_week=min_day
            )
            assert period.day_of_week == min_day
        except ValidationError:
            pytest.fail("不應該對最小的星期值引發驗證錯誤")
        
        # 最大值測試
        try:
            period = TimePeriodModel(
                id=test_id,
                business_id=business_id,
                start_time=time(9, 0),
                end_time=time(17, 0),
                day_of_week=max_day
            )
            assert period.day_of_week == max_day
        except ValidationError:
            pytest.fail("不應該對最大的星期值引發驗證錯誤")


class TestEmptyOrMinimalValues:
    """測試空值或最小值情況"""

    def test_empty_optional_fields(self):
        """測試所有可選欄位為空的情況"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 建立只有必填欄位的用戶模型
        try:
            user = UserModel(
                id=test_id,
                business_id=business_id,
                email="test@example.com",
                name="測試用戶",
                role=UserRole.STAFF
                # 所有可選欄位未提供
            )
            # 確認所有可選欄位都是 None 或預設值
            assert user.phone is None
            assert user.profile_data is None
            assert user.password_hash is None
            assert user.last_login is None
            assert user.line_user_id is None
            assert user.is_active is True  # 預設值
            assert user.email_verified is False  # 預設值
        except ValidationError:
            pytest.fail("不應該對最小必填欄位模型引發驗證錯誤")

    def test_empty_string_values(self):
        """測試空字串值"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 測試名稱為空字串
        with pytest.raises(ValidationError) as exc_info:
            UserModel(
                id=test_id,
                business_id=business_id,
                email="test@example.com",
                name="",  # 空字串
                role=UserRole.STAFF
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("name" in str(err).lower() for err in error_details)


class TestMixedValidationScenarios:
    """測試混合驗證場景"""

    def test_valid_and_invalid_fields_together(self):
        """測試同時存在有效和無效欄位的情況"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 部分有效、部分無效的欄位
        with pytest.raises(ValidationError) as exc_info:
            user = UserModel(
                id=test_id,
                business_id=business_id,
                email="test@example.com",  # 有效
                name="測試用戶",  # 有效
                role="invalid_role",  # 無效
                phone="12345"  # 有效
            )
        
        # 檢查錯誤訊息是否包含預期的內容
        error_details = exc_info.value.errors()
        assert any("role" in str(err).lower() for err in error_details)
        # 確認只有 role 欄位有錯誤
        assert len(error_details) == 1

    def test_cascade_error_dependencies(self):
        """測試錯誤級聯依賴關係"""
        # 準備測試數據
        test_id = uuid.uuid4()
        
        # 在 BookingModel 中，多個 UUID 欄位皆為無效格式
        with pytest.raises(ValidationError) as exc_info:
            booking = BookingModel(
                id=test_id,
                business_id="invalid-uuid-1",  # 無效
                customer_id="invalid-uuid-2",  # 無效
                service_id="invalid-uuid-3",   # 無效
                period_id="invalid-uuid-4",    # 無效
                start_time=datetime(2025, 2, 15, 10, 0),
                end_time=datetime(2025, 2, 15, 11, 0),
                status=BookingStatus.PENDING
            )
        
        # 檢查錯誤訊息是否包含所有無效 UUID 的信息
        error_details = exc_info.value.errors()
        assert len(error_details) >= 4  # 至少有 4 個錯誤（每個無效 UUID 一個）


class TestRecursiveDataValidation:
    """測試遞迴數據驗證"""

    def test_nested_json_structure(self):
        """測試嵌套 JSON 結構"""
        # 準備測試數據
        test_id = uuid.uuid4()
        
        # 具有嵌套結構的設定
        valid_settings = {
            "notifications": {
                "email": True,
                "sms": False,
                "preferences": {
                    "language": "zh-TW",
                    "format": "html"
                }
            },
            "display": {
                "theme": "dark",
                "timezone": "Asia/Taipei"
            }
        }
        
        # 測試有效的嵌套結構
        try:
            business = BusinessModel(
                id=test_id,
                name="測試商家",
                settings=valid_settings
            )
            assert business.settings == valid_settings
        except ValidationError:
            pytest.fail("不應該對有效的嵌套 JSON 結構引發驗證錯誤")
        
        # 無效的嵌套結構 (具有不允許的類型)
        invalid_settings = {
            "notifications": {
                "email": "yes",  # 應該是布林值而非字串
                "preferences": None  # 應該是字典而非 None
            }
        }
        
        # 注意：這可能不會引發錯誤，因為 Pydantic 可能會隱式轉換一些值
        try:
            business = BusinessModel(
                id=test_id,
                name="測試商家",
                settings=invalid_settings
            )
            # 檢查是否發生了隱式轉換
            assert isinstance(business.settings["notifications"]["email"], bool)
        except ValidationError as e:
            # 如果引發錯誤，至少確認錯誤與 settings 相關
            error_details = e.errors()
            assert any("settings" in str(err).lower() for err in error_details)