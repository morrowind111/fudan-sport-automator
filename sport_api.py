import json
import os

import aiohttp
from geopy.point import Point

import hashlib
import json

def generate_sign(params):
    """
    根据复旦体育小程序的加密逻辑生成 sign
    """
    data = params.copy()
    
    data.pop('sign', None)
    data.pop('filter', None)
    
    sorted_keys = sorted(data.keys())
    
    values = []
    for key in sorted_keys:
        val = data[key]
        if isinstance(val, (dict, list)):
            formatted_val = json.dumps(val, separators=(',', ':'), ensure_ascii=False)
        elif isinstance(val, bool):
            formatted_val = "true" if val else "false"
        elif val is None:
            formatted_val = "null"
        else:
            formatted_val = str(val)
        
        values.append(formatted_val)
    
    joined_values = ",".join(values)
    
    secret_key = "moveclub123123123"
    string_to_sign = secret_key + joined_values
    
    md5_hash = hashlib.md5()
    md5_hash.update(string_to_sign.encode('utf-8'))
    return md5_hash.hexdigest()

def _get_arg_from_env_or_json(arg_name, default=None):
    value = os.getenv(arg_name)
    if value is None or not value.strip():
        # Try loading from setting.json
        try:
            with open('settings.json', 'r', encoding='utf-8') as fp:
                value = json.load(fp)[arg_name]
        except Exception:
            value = default
    return value


async def get_routes():
    route_url = 'https://sport.fudan.edu.cn/sapi/route/list'
    params = {'userid': _get_arg_from_env_or_json('USER_ID'),
              'token': _get_arg_from_env_or_json('FUDAN_SPORT_TOKEN')}
    async with aiohttp.request('GET', route_url, params=params) as response:
        data = await response.json()
    try:
        route_data_list = filter(lambda route: route['points'] is not None and len(route['points']) >= 1,
                                 data['data']['list'])
        return [FudanRoute(route_data) for route_data in route_data_list]
    except Exception:
        print(f"ERROR: {data['message']}")
        exit(1)


class FudanAPI:
    def __init__(self, route):
        self.route = route
        self.user_id = _get_arg_from_env_or_json('USER_ID')
        self.token = _get_arg_from_env_or_json('FUDAN_SPORT_TOKEN')
        self.system = _get_arg_from_env_or_json('PLATFORM_OS', 'iOS 2016.3.1')
        self.device = _get_arg_from_env_or_json('PLATFORM_DEVICE', 'iPhone|iPhone 13<iPhone14,5>')
        self.run_id = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.62(0x18003e3a) NetType/WIFI Language/zh_CN',
            'Referer': 'https://servicewechat.com/wx07ea19ad2c2b98f3/18/page-frame.html',
            'Connection': 'keep-alive',
            'content-type': 'application/json'
        }

    async def start(self):
        start_url = 'https://sport.fudan.edu.cn/sapi/run/start'
        params = {'userid': self.user_id,
                  'token': self.token,
                  'route_id': self.route.id,
                  'route_type': self.route.type,
                  'system': self.system,
                  'device': self.device,
                  'lng': self.route.start_point.longitude,
                  'lat': self.route.start_point.latitude}
        params['sign'] = generate_sign(params)
        async with aiohttp.request('GET', start_url, params=params, headers=self.headers) as response:
            data = await response.json()
        try:
            self.run_id = data['data']['run_id']
        except Exception:
            print(f"ERROR: {data['message']}")
            exit(1)

    async def update(self, point):
        update_url = 'https://sport.fudan.edu.cn/sapi/run/point'
        params = {'userid': self.user_id,
                  'token': self.token,
                  'run_id': self.run_id,
                  'lng': point.longitude,
                  'lat': point.latitude}
        params['sign'] = generate_sign(params)
        async with aiohttp.request('GET', update_url, params=params, headers=self.headers) as response:
            try:
                data = await response.json()
                return data['message']
            except Exception:
                return await response.read()

    async def finish(self, point):
        finish_url = 'https://sport.fudan.edu.cn/sapi/run/finish'
        params = {'userid': self.user_id,
                  'token': self.token,
                  'run_id': self.run_id,
                  'system': self.system,
                  'device': self.device,
                  'lng': point.longitude,
                  'lat': point.latitude}
        params['sign'] = generate_sign(params)
        async with aiohttp.request('GET', finish_url, params=params, headers=self.headers) as response:
            data = await response.json()
        return data['message']


class FudanRoute:
    def __init__(self, data):
        self.id = data['route_id']
        self.name = data['name']
        self.type = data['types'][0]
        self.start_point = Point(data['points'][0]['lat'],
                                 data['points'][0]['lng'])

    def pretty_print(self):
        print(f"#{self.id}: {self.name}")
