-- 安全删除用户的SQL脚本
-- 使用方法：先设置要删除的用户ID，然后执行

-- 设置要删除的用户ID
SET @user_id_to_delete = 14;  -- 修改这里的ID为你要删除的用户ID

-- 1. 先删除用户的活动日志记录
DELETE FROM operator_activity_logs WHERE operator_id = @user_id_to_delete;

-- 2. 删除系统日志中的相关记录
DELETE FROM system_logs WHERE operator_id = @user_id_to_delete;

-- 3. 检查是否还有其他外键约束
-- 如果有exchange_transactions表的外键约束，也需要删除
-- DELETE FROM exchange_transactions WHERE operator_id = @user_id_to_delete;

-- 4. 最后删除用户
DELETE FROM operators WHERE id = @user_id_to_delete;

-- 验证删除结果
SELECT 'User deletion completed' as result;
SELECT COUNT(*) as remaining_activity_logs FROM operator_activity_logs WHERE operator_id = @user_id_to_delete;
SELECT COUNT(*) as remaining_system_logs FROM system_logs WHERE operator_id = @user_id_to_delete; 