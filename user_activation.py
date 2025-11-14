import requests
import json
from typing import Dict, Optional, List
from datetime import datetime


class UserActivationService:
    """Office 365 用户激活信息查询服务"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def query_all_users_activation(self, subscription_id: str) -> Dict:
        """查询订阅下所有用户的 Office 365 激活信息"""
        subscription = self.config_manager.get_subscription(subscription_id)
        if not subscription:
            return {
                'success': False,
                'error': '订阅不存在'
            }
        
        user_create_config = subscription.get('user_create_config')
        if not user_create_config:
            return {
                'success': False,
                'error': '该订阅未配置用户管理功能，无法查询激活信息'
            }
        
        try:
            # 导入 UserLister 来获取用户列表
            from user_lister import UserLister
            user_lister = UserLister(self.config_manager)
            
            # 获取所有用户
            users_result = user_lister.list_users(subscription_id)
            if not users_result['success']:
                return users_result
            
            users = users_result['data']['users']
            print(f"[批量激活查询] 找到 {len(users)} 个用户")
            
            # 查询每个用户的激活信息
            all_activations = []
            for user in users:
                object_id = user.get('object_id')
                if not object_id:
                    # 如果用户列表中没有 object_id，跳过
                    continue
                
                print(f"[批量激活查询] 查询用户: {user['display_name']}")
                
                # 获取激活数据
                activation_result = self.fetch_activation_data(subscription_id, object_id)
                if activation_result['success']:
                    activation_data = self.parse_activation_response(activation_result['data'])
                    
                    # 只添加有激活设备的用户
                    machines = activation_data.get('machines', [])
                    active_computers = activation_data.get('active_computers', 0)
                    active_devices = activation_data.get('active_devices', 0)
                    
                    # 如果有激活的电脑或设备，或者有设备列表，则添加
                    if machines or active_computers > 0 or active_devices > 0:
                        all_activations.append({
                            'user_info': {
                                'display_name': user['display_name'],
                                'user_principal_name': user['user_principal_name'],
                                'email': user.get('email', ''),
                                'object_id': object_id
                            },
                            'activation_info': activation_data
                        })
                        print(f"[批量激活查询] ✅ {user['display_name']} 有激活设备")
                    else:
                        print(f"[批量激活查询] ⏭️ {user['display_name']} 无激活设备，跳过")
            
            print(f"[批量激活查询] 完成，共 {len(all_activations)} 个用户有激活设备")
            
            return {
                'success': True,
                'data': {
                    'total_users': len(users),
                    'users_with_activation_count': len(all_activations),
                    'users_with_activation': all_activations
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'批量查询激活信息失败: {str(e)}'
            }
    
    def query_user_activation(self, subscription_id: str, username: str) -> Dict:
        """查询用户的 Office 365 激活信息"""
        subscription = self.config_manager.get_subscription(subscription_id)
        if not subscription:
            return {
                'success': False,
                'error': '订阅不存在'
            }
        
        user_create_config = subscription.get('user_create_config')
        if not user_create_config:
            return {
                'success': False,
                'error': '该订阅未配置用户管理功能，无法查询激活信息'
            }
        
        try:
            # 步骤1: 获取用户的 ObjectId
            object_id_result = self.get_user_object_id(subscription_id, username)
            if not object_id_result['success']:
                return object_id_result
            
            user_info = object_id_result['user_info']
            object_id = user_info['object_id']
            
            print(f"[激活查询] 找到用户: {user_info['display_name']} (ObjectId: {object_id})")
            
            # 步骤2: 获取激活数据
            activation_result = self.fetch_activation_data(subscription_id, object_id)
            if not activation_result['success']:
                return activation_result
            
            # 步骤3: 解析激活数据
            activation_data = self.parse_activation_response(activation_result['data'])
            
            return {
                'success': True,
                'data': {
                    'user_info': user_info,
                    'activation_info': activation_data
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'查询激活信息失败: {str(e)}'
            }
    
    def get_user_object_id(self, subscription_id: str, username: str) -> Dict:
        """通过用户列表API查找用户的ObjectId"""
        subscription = self.config_manager.get_subscription(subscription_id)
        user_create_config = subscription.get('user_create_config')
        
        try:
            headers = user_create_config['headers'].copy()
            headers['content-type'] = 'application/json'
            
            cookies_str = user_create_config['cookies']
            
            # 如果用户创建配置的 cookie 为空，尝试使用订阅配置的 cookie
            if not cookies_str or cookies_str.strip() == '':
                cookies_str = subscription.get('cookies', '')
                if cookies_str:
                    print(f"[查询激活] 用户创建配置的 cookie 为空，使用订阅配置的 cookie")
            
            cookies = {}
            if cookies_str:
                for cookie in cookies_str.split('; '):
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        cookies[key] = value
            
            api_url = user_create_config['api_url']
            parts = api_url.split('/')
            base_url = f"{parts[0]}//{parts[2]}"
            list_users_url = f"{base_url}/admin/api/Users/ListUsers"
            
            payload = {
                "ListAction": -1,
                "SortDirection": 0,
                "ListContext": None,
                "SortPropertyName": "DisplayName",
                "SearchText": username,
                "SelectedView": "",
                "SelectedViewType": "",
                "ServerContext": None,
                "MSGraphFilter": {
                    "skuIds": [],
                    "locations": [],
                    "domains": []
                }
            }
            
            print(f"[激活查询] 搜索用户: {username}")
            
            response = requests.post(
                list_users_url,
                headers=headers,
                cookies=cookies,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 401 or response.status_code == 403:
                return {
                    'success': False,
                    'error': '认证失败，Cookie 可能已过期'
                }
            
            if response.status_code not in [200, 201]:
                return {
                    'success': False,
                    'error': f'API 返回错误状态码: {response.status_code}'
                }
            
            data = response.json()
            users = data.get('Users', [])
            
            matched_user = None
            for user in users:
                user_principal_name = user.get('UserPrincipalName', '')
                display_name = user.get('DisplayName', '')
                
                if (username.lower() in user_principal_name.lower() or 
                    username.lower() in display_name.lower()):
                    matched_user = user
                    break
            
            if not matched_user:
                return {
                    'success': False,
                    'error': f'未找到用户: {username}'
                }
            
            return {
                'success': True,
                'user_info': {
                    'object_id': matched_user.get('ObjectId', ''),
                    'display_name': matched_user.get('DisplayName', ''),
                    'user_principal_name': matched_user.get('UserPrincipalName', ''),
                    'email': matched_user.get('Mail', '')
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'查找用户失败: {str(e)}'
            }
    
    def fetch_activation_data(self, subscription_id: str, object_id: str) -> Dict:
        """调用officeInstalls API获取激活数据"""
        subscription = self.config_manager.get_subscription(subscription_id)
        user_create_config = subscription.get('user_create_config')
        
        try:
            headers = user_create_config['headers'].copy()
            
            cookies_str = user_create_config['cookies']
            
            # 如果用户创建配置的 cookie 为空，尝试使用订阅配置的 cookie
            if not cookies_str or cookies_str.strip() == '':
                cookies_str = subscription.get('cookies', '')
                if cookies_str:
                    print(f"[获取激活数据] 用户创建配置的 cookie 为空，使用订阅配置的 cookie")
            
            cookies = {}
            if cookies_str:
                for cookie in cookies_str.split('; '):
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        cookies[key] = value
            
            api_url = user_create_config['api_url']
            parts = api_url.split('/')
            base_url = f"{parts[0]}//{parts[2]}"
            activation_url = f"{base_url}/admin/api/users/{object_id}/officeInstalls"
            
            print(f"[激活查询] 查询激活信息: {activation_url}")
            
            response = requests.get(
                activation_url,
                headers=headers,
                cookies=cookies,
                timeout=30
            )
            
            if response.status_code == 401 or response.status_code == 403:
                return {
                    'success': False,
                    'error': '认证失败，Cookie 可能已过期'
                }
            
            if response.status_code not in [200, 201]:
                return {
                    'success': False,
                    'error': f'API 返回错误状态码: {response.status_code}'
                }
            
            data = response.json()
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'获取激活数据失败: {str(e)}'
            }
    
    def parse_activation_response(self, response: Dict) -> Dict:
        """解析API响应，提取设备和激活信息"""
        try:
            software_machine_details = response.get('SoftwareMachineDetails', [])
            
            if not software_machine_details:
                return {
                    'active_computers': 0,
                    'total_computers': 0,
                    'active_devices': 0,
                    'total_devices': 0,
                    'machines': []
                }
            
            machine_details = software_machine_details[0].get('MachineDetails', {})
            machines_list = machine_details.get('Machines', [])
            
            parsed_machines = []
            for machine in machines_list:
                machine_type_map = {
                    1: 'Windows',
                    2: 'Mac',
                    3: 'Mobile',
                    4: 'Tablet',
                    5: 'iOS',
                    6: 'Android'
                }
                
                license_status_map = {
                    0: '未激活',
                    1: '已激活'
                }
                
                machine_type = machine.get('MachineType', 0)
                license_status = machine.get('LicenseStatus', 0)
                
                parsed_machines.append({
                    'machine_name': machine.get('MachineName', '未知'),
                    'machine_os': machine.get('MachineOs', '未知'),
                    'machine_type': machine_type_map.get(machine_type, '未知'),
                    'machine_type_code': machine_type,
                    'license_status': license_status_map.get(license_status, '未知'),
                    'license_status_code': license_status,
                    'last_license_requested': machine.get('LastLicenseRequestedDate', ''),
                    'office_version': machine.get('OfficeMajorVersion', 0)
                })
            
            return {
                'active_computers': machine_details.get('ActiveComputers', 0),
                'total_computers': machine_details.get('TotalComputers', 0),
                'active_devices': machine_details.get('ActiveDevices', 0),
                'total_devices': machine_details.get('TotalDevices', 0),
                'machines': parsed_machines
            }
            
        except Exception as e:
            print(f"[激活查询] 解析响应失败: {str(e)}")
            return {
                'active_computers': 0,
                'total_computers': 0,
                'active_devices': 0,
                'total_devices': 0,
                'machines': []
            }
    
    def format_activation_message(self, user_info: Dict, activation_data: Dict) -> str:
        """格式化输出消息（用于微信通知）"""
        machines = activation_data.get('machines', [])
        active_computers = activation_data.get('active_computers', 0)
        total_computers = activation_data.get('total_computers', 0)
        active_devices = activation_data.get('active_devices', 0)
        total_devices = activation_data.get('total_devices', 0)
        
        message_lines = [
            "📱 Office 365 激活信息\n",
            f"👤 用户: {user_info['display_name']}",
            f"📧 邮箱: {user_info['user_principal_name']}\n",
            "💻 设备激活情况",
            f"已激活: {active_computers} / {total_computers} 台电脑",
            f"已激活: {active_devices} / {total_devices} 台移动设备\n"
        ]
        
        if machines:
            message_lines.append("📋 设备列表:")
            for i, machine in enumerate(machines, 1):
                status_icon = '✅' if machine['license_status_code'] == 1 else '❌'
                last_requested = machine['last_license_requested']
                
                if last_requested:
                    try:
                        dt = datetime.fromisoformat(last_requested.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        formatted_time = last_requested[:16].replace('T', ' ')
                else:
                    formatted_time = '未知'
                
                message_lines.append(
                    f"{i}. {machine['machine_name']}\n"
                    f"   {machine['machine_os']}\n"
                    f"   {status_icon} {machine['license_status']}\n"
                    f"   最后请求: {formatted_time}"
                )
        else:
            message_lines.append("暂无激活设备")
        
        return "\n".join(message_lines)
