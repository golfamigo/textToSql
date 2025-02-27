# N8N預約系統資料庫結構

本目錄包含了N8N預約系統的資料庫表格結構。以下是主要表及​​其關係：

## 表結構概述

1. **n8n_booking_businesses**: 商家資訊表
 - 系統中的商家/機構基本訊息

2. **n8n_booking_users**: 系統使用者表
 - 系統的使用者(管理者、員工、顧客)
 - 外鍵: `business_id` -> `n8n_booking_businesses.id`

3. **n8n_booking_services**: 服務項目表
 - 商家提供的各種服務
 - 外鍵: `business_id` -> `n8n_booking_businesses.id`
 - 外鍵: `business_hours_override_id` -> `n8n_booking_businesses.id`

4. **n8n_booking_staff_services**: 員工服務關聯表
 - 連結員工與其可提供的服務
 - 外鍵: `staff_id` -> `n8n_booking_users.id`
 - 外鍵: `service_id` -> `n8n_booking_services.id`

5. **n8n_booking_time_periods**: 預約時段表
 - 定義可預約的時段
 - 外鍵: `business_id` -> `n8n_booking_businesses.id`

6. **n8n_booking_service_period_restrictions**: 服務時段限製表
 - 定義特定服務在特定時段是否可用
 - 外鍵: `service_id` -> `n8n_booking_services.id`
 - 外鍵: `period_id` -> `n8n_booking_time_periods.id`

7. **n8n_booking_staff_availability**: 員工可用時間表
 - 員工的工作/可用時間
 - 外鍵: `staff_id` -> `n8n_booking_users.id`
 - 外鍵: `business_id` -> `n8n_booking_businesses.id`

8. **n8n_booking_bookings**: 預約表
 - 客戶的預約記錄
 - 外鍵: `business_id` -> `n8n_booking_businesses.id`
 - 外鍵: `service_id` -> `n8n_booking_services.id`
 - 外鍵: `period_id` -> `n8n_booking_time_periods.id`
 - 外鍵: `staff_id` -> `n8n_booking_users.id`

9. **n8n_booking_history**: 預約狀態變更歷史
 - 記錄預約狀態的變更歷史
 - 外鍵: `booking_id` -> `n8n_booking_bookings.id`

## 自訂類型

- **user_role**: 使用者角色枚舉類型 ('admin', 'staff', 'customer')
- **availability_type**: 可用性類型列舉 ('available', 'unavailable')

## 關係圖

```
n8n_booking_businesses <-- n8n_booking_users
 <-- n8n_booking_services
 <-- n8n_booking_time_periods
 <-- n8n_booking_staff_availability
 <-- n8n_booking_bookings

n8n_booking_users <-- n8n_booking_staff_services
 <-- n8n_booking_staff_availability
 <-- n8n_booking_bookings

n8n_booking_services <-- n8n_booking_staff_services
 <-- n8n_booking_service_period_restrictions
 <-- n8n_booking_bookings

n8n_booking_time_periods <-- n8n_booking_service_period_restrictions
 <-- n8n_booking_bookings

n8n_booking_bookings <-- n8n_booking_history
```