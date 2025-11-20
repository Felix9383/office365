import requests
import json
from typing import Dict, Optional


class UserCreator:
    """Office 365 用户创建器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def _assign_license(self, base_url: str, headers: dict, cookies: dict, 
                       object_id: str, subscription: dict) -> Dict:
        """为用户分配许可证"""
        try:
            # 从订阅数据中获取可用的许可证
            subscription_data = subscription.get('subscription_data', {})
            
            # 查找有可用许可证的产品
            available_licenses = []
            for product in subscription_data.get('Skus', []):
                sku_id = product.get('SkuId')
                available = product.get('Available', 0)
                
                if sku_id and available > 0:
                    available_licenses.append({
                        'SkuId': sku_id,
                        'SkuPartNumber': product.get('SkuPartNumber', ''),
                        'Available': available
                    })
            
            if not available_licenses:
                return {
                    'success': False,
                    'message': '没有可用的许可证'
                }
            
            # 使用第一个可用的许可证
            license_to_assign = available_licenses[0]
            print(f"[分配许可证] 使用许可证: {license_to_assign['SkuPartNumber']} (SKU: {license_to_assign['SkuId']})")
            
            # 构建分配许可证的 API URL
            assign_license_url = f"{base_url}/admin/api/users/{object_id}/assignlicense"
            
            # 构建请求体
            payload = {
                "AddLicenses": [{
                    "SkuId": license_to_assign['SkuId'],
                    "DisabledServicePlans": []
                }],
                "RemoveLicenses": []
            }
            
            print(f"[分配许可证] API URL: {assign_license_url}")
            print(f"[分配许可证] Payload: {json.dumps(payload, ensure_ascii=False)}")
            
            # 发送请求
            response = requests.post(
                assign_license_url,
                headers=headers,
                cookies=cookies,
                json=payload,
                timeout=30
            )
            
            print(f"[分配许可证] 响应状态码: {response.status_code}")
            print(f"[分配许可证] 响应内容: {response.text[:500]}")
            
            if response.status_code in [200, 201, 204]:
                return {
                    'success': True,
                    'message': f'已分配许可证: {license_to_assign["SkuPartNumber"]}'
                }
            else:
                return {
                    'success': False,
                    'message': f'分配许可证失败 (状态码: {response.status_code})'
                }
                
        except Exception as e:
            print(f"[分配许可证] 错误: {str(e)}")
            return {
                'success': False,
                'message': f'分配许可证时出错: {str(e)}'
            }
    
    def create_user(self, subscription_id: str, username: str, password: str) -> Dict:
        """创建 Office 365 用户"""
        subscription = self.config_manager.get_subscription(subscription_id)
        if not subscription:
            return {
                'success': False,
                'error': '订阅不存在'
            }
        
        # 检查是否配置了用户创建配置
        user_create_config = subscription.get('user_create_config')
        if not user_create_config:
            return {
                'success': False,
                'error': '该订阅未配置用户创建功能，请在设置中添加用户创建配置'
            }
        
        try:
            # 使用用户创建配置中的信息
            headers = user_create_config['headers'].copy()
            headers['content-type'] = 'application/json'
            
            cookies_str = user_create_config['cookies']
            
            # 如果用户创建配置的 cookie 为空，尝试使用订阅配置的 cookie
            if not cookies_str or cookies_str.strip() == '':
                cookies_str = subscription.get('cookies', '')
                if cookies_str:
                    print(f"[创建用户] 用户创建配置的 cookie 为空，使用订阅配置的 cookie")
                else:
                    return {
                        'success': False,
                        'error': '未找到有效的 Cookie 配置，请检查订阅配置或用户创建配置'
                    }
            
            # 将 cookies 字符串转换为字典
            cookies = {}
            if cookies_str:
                for cookie in cookies_str.split('; '):
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        cookies[key] = value
            
            # 使用用户创建配置中的 API URL
            create_user_url = user_create_config['api_url']
            
            # 提取基础 URL
            parts = create_user_url.split('/')
            base_url = f"{parts[0]}//{parts[2]}"
            
            print(f"[创建用户] API URL: {create_user_url}")
            
            # 从用户创建配置的原始 curl 命令中提取请求体
            user_create_curl = subscription.get('user_create_curl', '')
            
            if not user_create_curl or user_create_curl.strip() == '':
                print(f"[创建用户] 错误: 未配置用户创建 curl 命令")
                return {
                    'success': False,
                    'error': '该订阅未配置用户创建 curl 命令，请在设置中添加完整的用户创建 curl 命令（包含 --data-raw 参数）'
                }
            
            # 提取 --data-raw 后的 JSON 数据
            import re
            
            print(f"[创建用户] curl 命令长度: {len(user_create_curl)}")
            print(f"[创建用户] curl 命令前100字符: {user_create_curl[:100]}")
            
            # 尝试多种模式匹配
            data_match = re.search(r'--data-raw\s+\$?\'(.+?)\'(?:\s+-|$)', user_create_curl, re.DOTALL)
            if not data_match:
                data_match = re.search(r'--data-raw\s+\$?"(.+?)"(?:\s+-|$)', user_create_curl, re.DOTALL)
            if not data_match:
                data_match = re.search(r'--data-raw\s+(.+?)(?:\s+-H|\s+--|\s+$)', user_create_curl, re.DOTALL)
            
            if not data_match:
                print(f"[创建用户] 错误: 无法从 curl 命令中提取请求体")
                print(f"[创建用户] 提示: 请确保 curl 命令包含 --data-raw 参数")
                return {
                    'success': False,
                    'error': '无法从用户创建 curl 命令中提取请求体数据，请确保 curl 命令包含 --data-raw 参数'
                }
            
            # 解析原始请求体
            raw_data = data_match.group(1).strip()
            print(f"[创建用户] 提取到的数据长度: {len(raw_data)}")
            
            # 处理转义字符 - 将 \r\n 等转义序列替换为实际字符
            # 但保留 JSON 中的合法转义（如 \"）
            try:
                # 先尝试直接解析
                template_data = json.loads(raw_data)
                print(f"[创建用户] 成功解析模板数据")
            except json.JSONDecodeError as e:
                # 如果失败，尝试处理转义字符
                print(f"[创建用户] 首次解析失败，尝试处理转义字符")
                try:
                    # 使用 Python 的字符串字面量解析来处理转义
                    # 将字符串用引号包裹后用 ast.literal_eval 解析
                    import codecs
                    decoded_data = codecs.decode(raw_data, 'unicode_escape')
                    template_data = json.loads(decoded_data)
                    print(f"[创建用户] 处理转义后成功解析")
                except Exception as e2:
                    print(f"[创建用户] 错误: 解析 JSON 失败 - {str(e)}")
                    print(f"[创建用户] 原始数据前200字符: {raw_data[:200]}")
                    print(f"[创建用户] 错误位置附近: {raw_data[max(0, e.pos-50):min(len(raw_data), e.pos+50)]}")
                    return {
                        'success': False,
                        'error': f'用户创建配置中的请求体格式不正确: {str(e)}'
                    }
            
            # 从模板中提取域名
            template_upn = template_data.get('UserPrincipalName', '')
            if '@' in template_upn:
                domain = template_upn.split('@')[1]
            else:
                domain = "dfem.net"  # 默认域名
            
            user_principal_name = f"{username}@{domain}"
            
            print(f"[创建用户] 用户邮箱: {user_principal_name}")
            print(f"[创建用户] 使用域名: {domain}")
            
            # 使用模板中的 Products 和 AdminRoles
            products = template_data.get('Products', [])
            admin_roles = template_data.get('AdminRoles', [])
            
            # 构建请求体 - 使用模板结构
            payload = {
                "FirstName": template_data.get('FirstName', ''),
                "JobTitle": template_data.get('JobTitle', ''),
                "LastName": template_data.get('LastName', ''),
                "DisplayName": username,
                "UserPrincipalName": user_principal_name,
                "Office": template_data.get('Office', ''),
                "OfficePhone": template_data.get('OfficePhone', ''),
                "MobilePhone": template_data.get('MobilePhone', ''),
                "FaxNumber": template_data.get('FaxNumber', ''),
                "City": template_data.get('City', ''),
                "CountryRegion": template_data.get('CountryRegion', ''),
                "StateProvince": template_data.get('StateProvince', ''),
                "Department": template_data.get('Department', ''),
                "StreetAddress": template_data.get('StreetAddress', ''),
                "ZipOrPostalCode": template_data.get('ZipOrPostalCode', ''),
                "ForceChangePassword": True,
                "SendPasswordEmail": False,
                "Password": password,
                "AdminRoles": admin_roles,
                "UsageLocation": template_data.get('UsageLocation', 'CN'),
                "Products": products,
                "CreateUserWithNoLicense": template_data.get('CreateUserWithNoLicense', False)
            }
            
            if products:
                product_names = [p.get('SkuPartNumber', p.get('ProductSkuId', '')) for p in products if isinstance(p, dict)]
                print(f"[创建用户] 将分配许可证: {product_names}")
            
            print(f"[创建用户] 发送请求...")
            print(f"[创建用户] Payload: {json.dumps(payload, ensure_ascii=False)[:200]}...")
            
            # 发送请求
            response = requests.post(
                create_user_url,
                headers=headers,
                cookies=cookies,
                json=payload,
                timeout=30
            )
            
            print(f"[创建用户] 响应状态码: {response.status_code}")
            print(f"[创建用户] 响应内容: {response.text[:500]}")
            
            # 检查响应状态
            if response.status_code == 401 or response.status_code == 403:
                return {
                    'success': False,
                    'error': 'auth_failure',
                    'message': '认证失败，Cookie 可能已过期'
                }
            
            # 200 和 201 都是成功状态码
            if response.status_code not in [200, 201]:
                try:
                    error_data = response.json()
                    error_message = error_data.get('Message', '') or f"Code: {error_data.get('Code', 'unknown')}"
                    return {
                        'success': False,
                        'error': 'api_error',
                        'message': f'API 返回错误状态码: {response.status_code}',
                        'details': error_message,
                        'response_data': error_data
                    }
                except:
                    return {
                        'success': False,
                        'error': 'api_error',
                        'message': f'API 返回错误状态码: {response.status_code}',
                        'details': response.text[:500]
                    }
            
            # 解析响应
            data = response.json()
            
            print(f"[创建用户] 响应数据: {json.dumps(data, ensure_ascii=False)}")
            
            # 检查是否创建成功
            if data.get('Status') == 0:  # 0 表示成功
                user_info = data.get('UserInfo', {})
                object_id = user_info.get('ObjectId', '')
                
                # 提取许可证名称
                license_names = []
                if products:
                    for p in products:
                        if isinstance(p, dict):
                            license_names.append(p.get('SkuPartNumber', p.get('ProductSkuId', '')))
                
                return {
                    'success': True,
                    'data': {
                        'username': username,
                        'user_principal_name': user_principal_name,
                        'display_name': user_info.get('DisplayName', username),
                        'object_id': object_id,
                        'password': password,
                        'licenses': license_names,
                        'licenses_info': user_info.get('Licenses', '')
                    }
                }
            else:
                # Status != 0 表示失败
                error_code = data.get('Code', 'unknown')
                error_message = data.get('Message', '') or f'错误代码: {error_code}'
                
                # 406 通常表示请求参数问题
                if error_code == '406':
                    error_message = '请求参数不正确或缺少必要信息（错误代码 406）'
                
                return {
                    'success': False,
                    'error': 'creation_failed',
                    'message': error_message,
                    'code': error_code,
                    'status': data.get('Status')
                }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'timeout',
                'message': '请求超时'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': 'network_error',
                'message': f'网络错误: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'unknown_error',
                'message': f'未知错误: {str(e)}'
            }
