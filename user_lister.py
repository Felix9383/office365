import requests
import json
from typing import Dict, List


class UserLister:
    """Office 365 用户查询器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def list_users(self, subscription_id: str) -> Dict:
        """查询 Office 365 用户列表"""
        subscription = self.config_manager.get_subscription(subscription_id)
        if not subscription:
            return {
                'success': False,
                'error': '订阅不存在'
            }
        
        # 检查是否配置了用户创建配置（使用相同的cookie）
        user_create_config = subscription.get('user_create_config')
        if not user_create_config:
            return {
                'success': False,
                'error': '该订阅未配置用户创建功能，无法查询用户'
            }
        
        try:
            # 使用用户创建配置中的认证信息
            headers = user_create_config['headers'].copy()
            headers['content-type'] = 'application/json'
            
            cookies_str = user_create_config['cookies']
            
            # 如果用户创建配置的 cookie 为空，尝试使用订阅配置的 cookie
            if not cookies_str or cookies_str.strip() == '':
                cookies_str = subscription.get('cookies', '')
                if cookies_str:
                    print(f"[查询用户] 用户创建配置的 cookie 为空，使用订阅配置的 cookie")
                else:
                    return {
                        'success': False,
                        'error': '未找到有效的 Cookie 配置'
                    }
            
            # 将 cookies 字符串转换为字典
            cookies = {}
            if cookies_str:
                for cookie in cookies_str.split('; '):
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        cookies[key] = value
            
            # 构建查询用户的 API URL
            api_url = user_create_config['api_url']
            parts = api_url.split('/')
            base_url = f"{parts[0]}//{parts[2]}"
            list_users_url = f"{base_url}/admin/api/Users/ListUsers"
            
            print(f"[查询用户] API URL: {list_users_url}")
            
            # 构建请求体
            payload = {
                "ListAction": -1,
                "SortDirection": 0,
                "ListContext": None,
                "SortPropertyName": "DisplayName",
                "SearchText": "",
                "SelectedView": "",
                "SelectedViewType": "",
                "ServerContext": None,
                "MSGraphFilter": {
                    "skuIds": [],
                    "locations": [],
                    "domains": []
                }
            }
            
            print(f"[查询用户] 发送请求...")
            
            # 发送请求
            response = requests.post(
                list_users_url,
                headers=headers,
                cookies=cookies,
                json=payload,
                timeout=30
            )
            
            print(f"[查询用户] 响应状态码: {response.status_code}")
            
            # 检查响应状态
            if response.status_code == 401 or response.status_code == 403:
                return {
                    'success': False,
                    'error': '认证失败，Cookie 可能已过期'
                }
            
            if response.status_code not in [200, 201]:
                return {
                    'success': False,
                    'error': f'API 返回错误状态码: {response.status_code}',
                    'details': response.text[:500]
                }
            
            # 解析响应
            data = response.json()
            
            users = data.get('Users', [])
            metadata = data.get('MetaData', {})
            
            print(f"[查询用户] 查询到 {len(users)} 个用户")
            
            # 提取用户信息
            user_list = []
            for user in users:
                user_list.append({
                    'object_id': user.get('ObjectId', ''),
                    'display_name': user.get('DisplayName', ''),
                    'user_principal_name': user.get('UserPrincipalName', ''),
                    'email': user.get('Mail', ''),
                    'licenses': user.get('Licenses', ''),
                    'has_license': user.get('HasLicense', False),
                    'signin_status': user.get('SigninStatus', ''),
                    'created_time': user.get('CreatedTime', ''),
                    'usage_location': user.get('UsageLocation', ''),
                    'first_name': user.get('FirstName', ''),
                    'last_name': user.get('LastName', ''),
                    'job_title': user.get('JobTitle', ''),
                    'department': user.get('Department', ''),
                    'mobile_phone': user.get('MobilePhone', ''),
                    'business_phones': user.get('BusinessPhones', '')
                })
            
            return {
                'success': True,
                'data': {
                    'users': user_list,
                    'total_count': metadata.get('DataCount', len(users)),
                    'is_last_page': metadata.get('IsLastPage', True)
                }
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': '请求超时'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'网络错误: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'未知错误: {str(e)}'
            }
