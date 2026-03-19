

# 微信系统 MySQL 确认信息 (2026-03-18 补充)

## 一、门禁进出明细查询

### 问题1: sign_type 字段含义
- **表**: `m_user_door_record_info`
- **字段**: `sign_type`
- **确认结果**: 0 = 进，1 = 出

### 问题2: user_no 与 user_number 对应关系
- **表**: `m_user_door_record_info`, `sys_user`
- **确认结果**: `user_no` 和 `user_number` 是一样的，都是学号
- **影响**: 可以直接在门禁记录表按学号查询，无需关联用户表

---

## 二、学生信息查询

### 问题3: sys_dept.leader 字段
- **表**: `sys_dept`
- **字段**: `leader`
- **确认结果**: 暂时没有用到

### 班主任信息获取
- **表**: `sys_user_dept`
- **字段**: `header_teacher = 1` 表示是班主任
- **关联关系**:
  - `sys_user_dept.user_id` → `sys_user.user_id`
  - `sys_user_dept.dept_id` → `sys_dept.dept_id`

### 问题4: 年级信息获取方式
- **确认结果**: 通过 `dept_name` 名称识别（如 "2024级"）

### 问题5: wx_address 表
- **表**: `wx_address`
- **用途**: 记录楼栋、楼层信息
- **字段**: `type` 字段注释了具体的含义

### 房间表关系
- **表**: `wx_room`
- **关联**:
  - `address_id` → 楼层 (`wx_address`)
  - `address_parent_id` → 楼栋 (`wx_address`)

### 床位表关系
- **表**: `wx_room_bed`
- **用途**: 记录床位与房间的关系
- **关联**: `room_id` → `wx_room.room_id`

---

## 三、确认后更新的SQL查询

### 3.1 门禁进出明细查询（简化版）

由于 user_no 就是学号，可以直接查询：

```sql
SELECT 
    id,
    user_no AS '学号',
    sign_type AS '进出类型',
    CASE sign_type WHEN 0 THEN '进' WHEN 1 THEN '出' END AS '进出说明',
    device_name AS '设备名称',
    record_time AS '进出时间'
FROM m_user_door_record_info
WHERE user_no = #{user_no}
ORDER BY record_time DESC
LIMIT 100;
```

### 3.2 班主任信息查询

```sql
SELECT 
    u.user_id,
    u.name AS '姓名',
    u.user_number AS '工号',
    d.dept_name AS '班级名称',
    '班主任' AS '职务'
FROM sys_user_dept ud
JOIN sys_user u ON ud.user_id = u.user_id
JOIN sys_dept d ON ud.dept_id = d.dept_id
WHERE ud.header_teacher = 1;
```

### 3.3 学生完整信息（含住宿）

```sql
SELECT 
    u.name AS '姓名',
    u.id_card AS '身份证号',
    u.user_number AS '学号',
    d.dept_name AS '班级',
    CASE WHEN r.room_id IS NOT NULL THEN '已入住' ELSE '未入住' END AS '住宿状态',
    a.name AS '楼栋',
    a2.name AS '楼层',
    r.room_name AS '房间号',
    rb.bed_name AS '床位号'
FROM sys_user u
LEFT JOIN sys_dept d ON u.dept_id = d.dept_id
LEFT JOIN wx_room_bed rb ON rb.user_id = u.user_id
LEFT JOIN wx_room r ON rb.room_id = r.room_id
LEFT JOIN wx_address a ON r.address_parent_id = a.id  -- 楼栋
LEFT JOIN wx_address a2 ON r.address_id = a2.id       -- 楼层
WHERE u.user_number = #{user_number};
```

---

## 四、核心表关系图

```
sys_user (用户)
  ├── user_id → sys_user_dept.user_id
  ├── user_number → m_user_door_record_info.user_no (学号)
  └── dept_id → sys_dept.dept_id

sys_dept (部门/班级)
  └── dept_id → sys_user_dept.dept_id

sys_user_dept (用户部门关联)
  ├── user_id → sys_user.user_id
  ├── dept_id → sys_dept.dept_id
  └── header_teacher = 1 → 班主任

m_user_door_record_info (门禁记录)
  └── user_no = sys_user.user_number (学号)

wx_address (楼栋/楼层)
  ├── id → wx_room.address_parent_id (楼栋)
  └── id → wx_room.address_id (楼层)

wx_room (房间)
  ├── address_parent_id → wx_address.id (楼栋)
  ├── address_id → wx_address.id (楼层)
  └── room_id → wx_room_bed.room_id

wx_room_bed (床位)
  ├── room_id → wx_room.room_id
  └── user_id → sys_user.user_id
```
