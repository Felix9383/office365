import requests
import json
from typing import Dict


class Notifier:
    """通知服务 - 支持自定义 Webhook"""
    
    def __init__(self, config: Dict):
        self.webhook_url = config.get('webhook_url', '')
        self.webhook_json = config.get('webhook_json', '')
    
    def send_notification(self, message: str) -> bool:
        """发送通知"""
        if not self.webhook_url:
            print(f"[通知] Webhook 未配置，跳过发送")
            return False
        
        try:
            # 解析 JSON 模板
            if self.webhook_json and self.webhook_json.strip():
                try:
                    # 检查是否为空字符串
                    if self.webhook_json.strip() == '':
                        raise json.JSONDecodeError("Empty string", "", 0)
                    
                    # 先尝试直接解析
                    payload = json.loads(self.webhook_json)
                    
                    # 替换消息变量
                    payload_str = json.dumps(payload, ensure_ascii=False)
                    payload_str = payload_str.replace('{title}', '订阅监控通知')
                    payload_str = payload_str.replace('{content}', message)
                    payload_str = payload_str.replace('{通知消息}', message)
                    payload = json.loads(payload_str)
                    
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"[通知] JSON 模板解析失败: {e}")
                    print(f"[通知] 模板内容: {repr(self.webhook_json[:100] if len(self.webhook_json) > 100 else self.webhook_json)}")
                    # 使用默认格式继续发送
                    payload = {
                        "title": "订阅监控通知",
                        "text": message
                    }
            else:
                # 默认格式
                payload = {
                    "title": "订阅监控通知",
                    "text": message
                }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"[通知] 发送成功: {message[:50]}...")
                return True
            else:
                print(f"[通知] 发送失败，状态码: {response.status_code}")
                print(f"[通知] 响应: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"[通知] 发送异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def notify_auth_failure(self, subscription_name: str) -> bool:
        """通知认证失败（Cookie 过期）"""
        content = (
            f"⚠️ Office 365 订阅监控告警\n\n"
            f"订阅名称: {subscription_name}\n"
            f"状态: Cookie 已失效\n"
            f"原因: 认证失败，请更新 Cookie 信息"
        )
        return self.send_notification(content)
    
    def notify_subscription_expired(self, subscription_name: str) -> bool:
        """通知订阅失效"""
        content = (
            f"❌ Office 365 订阅监控告警\n\n"
            f"订阅名称: {subscription_name}\n"
            f"状态: 订阅已失效\n"
            f"请及时处理"
        )
        return self.send_notification(content)
    
    def notify_expiration_warning(self, subscription_name: str, days_remaining: int) -> bool:
        """通知即将到期"""
        content = (
            f"⏰ Office 365 订阅监控提醒\n\n"
            f"订阅名称: {subscription_name}\n"
            f"状态: 即将到期\n"
            f"剩余天数: {days_remaining} 天\n"
            f"请及时续费"
        )
        return self.send_notification(content)
