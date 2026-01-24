"""检查链接可用性"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style
from tqdm import tqdm

from utils.cache import FileCache


class LinkChecker:
    """链接检查器"""
    
    def __init__(self, config, report):
        """初始化"""
        self.config = config
        self.report = report
        self.link_config = config.get('link_check', {})
        self.timeout = self.link_config.get('timeout', 10)
        self.retry = self.link_config.get('retry', 2)
        self.user_agent = self.link_config.get('user_agent', 
                                               'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        self.max_workers = config.get('concurrency', {}).get('max_workers', 4)
        self.cache = FileCache(config.get('cache', {}))
    
    def check_entries(self, bib_database):
        """检查条目"""
        print(f"{Fore.GREEN}[信息] 开始检查链接可用性{Style.RESET_ALL}")
        
        # 收集所有链接
        links_to_check = []
        for entry in bib_database.entries:
            entry_id = entry.get('ID', 'unknown')
            
            # 检查 url 字段
            if 'url' in entry:
                links_to_check.append((entry_id, 'url', entry['url']))
            
            # 检查 pdf 字段
            if 'pdf' in entry:
                links_to_check.append((entry_id, 'pdf', entry['pdf']))
        
        if not links_to_check:
            print(f"{Fore.YELLOW}[信息] 没有找到需要检查的链接{Style.RESET_ALL}")
            return bib_database
        
        print(f"{Fore.GREEN}[信息] 找到 {len(links_to_check)} 个链接需要检查{Style.RESET_ALL}")
        
        # 遍历检查
        if self.max_workers and self.max_workers > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self._check_link, entry_id, field, url)
                    for entry_id, field, url in links_to_check
                ]
                for _ in tqdm(as_completed(futures), total=len(futures), desc="检查链接", unit="链接"):
                    pass
        else:
            for entry_id, field, url in tqdm(links_to_check, desc="检查链接", unit="链接"):
                self._check_link(entry_id, field, url)
        
        dead_count = len(self.report.dead_links)
        if dead_count > 0:
            print(f"{Fore.RED}[警告] 发现 {dead_count} 个失效链接{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[成功] 所有链接都可访问{Style.RESET_ALL}")
        
        return bib_database
    
    def _check_link(self, entry_id, field, url):
        """检查单个链接"""
        if not url or not url.startswith('http'):
            self.report.add_dead_link(entry_id, field, url, '无效的 URL 格式')
            return

        cache_key = f"link:{url}"
        cached_status = self.cache.get(cache_key)
        if cached_status is not None:
            if cached_status != 'OK':
                self.report.add_dead_link(entry_id, field, url, cached_status)
            return
        
        # 尝试 HEAD 请求
        status = self._try_request(url, 'HEAD')
        
        # 如果 HEAD 失败，尝试 GET
        if status != 'OK':
            status = self._try_request(url, 'GET')
        
        # 如果仍然失败，记录
        if status != 'OK':
            self.report.add_dead_link(entry_id, field, url, status)

        self.cache.set(cache_key, status)
    
    def _try_request(self, url, method='HEAD'):
        """尝试请求"""
        for attempt in range(self.retry):
            try:
                if method == 'HEAD':
                    response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
                else:
                    response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                
                if response.status_code == 200:
                    return 'OK'
                elif response.status_code in [301, 302, 303, 307, 308]:
                    # 重定向，视为成功
                    return 'OK'
                elif response.status_code == 404:
                    return f'HTTP {response.status_code} Not Found'
                elif response.status_code == 403:
                    return f'HTTP {response.status_code} Forbidden'
                elif response.status_code >= 500:
                    # 服务器错误，重试
                    if attempt < self.retry - 1:
                        continue
                    return f'HTTP {response.status_code} Server Error'
                else:
                    return f'HTTP {response.status_code}'
            except requests.exceptions.Timeout:
                if attempt < self.retry - 1:
                    continue
                return '请求超时'
            except requests.exceptions.ConnectionError:
                if attempt < self.retry - 1:
                    continue
                return '连接错误'
            except Exception as e:
                if attempt < self.retry - 1:
                    continue
                return f'错误: {str(e)}'
        
        return '未知错误'
