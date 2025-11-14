#!/usr/bin/env python3
"""
配置文件修复工具
用于修复或重建损坏的 config.json 文件
"""

import json
import os
import sys
from datetime import datetime

def backup_config(config_path='config.json'):
    """备份现有配置文件"""
    if os.path.exists(config_path):
        backup_path = f"{config_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy(config_path, backup_path)
            print(f"✅ 已备份现有配置到: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"⚠️  备份失败: {e}")
            return None
    return None

def create_default_config(config_path='config.json'):
    """创建默认配置文件"""
    default_config = {
        "subscriptions": [],
        "notification": {
            "webhook_url": "",
            "webhook_json": "",
            "expiration_warning_days": 30
        },
        "login_password": "xiaokun567"
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"✅ 已创建默认配置文件: {config_path}")
        return True
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False

def validate_config(config_path='config.json'):
    """验证配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
            if not content:
                print("❌ 配置文件为空")
                return False
            
            config = json.loads(content)
            
            # 检查必要字段
            required_fields = ['subscriptions', 'notification', 'login_password']
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                print(f"⚠️  缺少必要字段: {', '.join(missing_fields)}")
                return False
            
            # 检查 notification 字段
            notification_fields = ['webhook_url', 'webhook_json', 'expiration_warning_days']
            missing_notification = [field for field in notification_fields 
                                   if field not in config.get('notification', {})]
            
            if missing_notification:
                print(f"⚠️  notification 缺少字段: {', '.join(missing_notification)}")
                return False
            
            print("✅ 配置文件格式正确")
            return True
            
    except FileNotFoundError:
        print("❌ 配置文件不存在")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def fix_config(config_path='config.json'):
    """修复配置文件"""
    print("=" * 60)
    print("配置文件修复工具")
    print("=" * 60)
    print()
    
    # 检查配置文件
    if not os.path.exists(config_path):
        print(f"📝 配置文件不存在: {config_path}")
        print("正在创建默认配置...")
        if create_default_config(config_path):
            print()
            print("✅ 修复完成！")
            return True
        else:
            print()
            print("❌ 修复失败")
            return False
    
    # 验证配置文件
    print(f"🔍 检查配置文件: {config_path}")
    if validate_config(config_path):
        print()
        print("✅ 配置文件正常，无需修复")
        return True
    
    # 需要修复
    print()
    print("⚠️  配置文件需要修复")
    
    # 询问用户
    response = input("是否备份并重建配置文件？(y/n): ").strip().lower()
    
    if response != 'y':
        print("❌ 用户取消操作")
        return False
    
    # 备份
    print()
    print("📦 备份现有配置...")
    backup_path = backup_config(config_path)
    
    # 重建
    print()
    print("📝 创建新的默认配置...")
    if create_default_config(config_path):
        print()
        print("=" * 60)
        print("✅ 修复完成！")
        print("=" * 60)
        print()
        print("注意事项:")
        print("1. 默认密码: xiaokun567")
        print("2. 需要重新配置 Webhook")
        print("3. 需要重新添加订阅")
        if backup_path:
            print(f"4. 旧配置已备份到: {backup_path}")
        print()
        return True
    else:
        print()
        print("❌ 修复失败")
        return False

def main():
    """主函数"""
    config_path = 'config.json'
    
    # 检查是否在正确的目录
    if not os.path.exists('app.py'):
        print("⚠️  警告: 当前目录下没有 app.py 文件")
        print("请确保在项目根目录下运行此脚本")
        print()
    
    success = fix_config(config_path)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
