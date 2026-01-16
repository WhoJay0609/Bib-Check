"""报告生成工具"""

from colorama import Fore, Style


class Report:
    """报告类"""
    
    def __init__(self):
        """初始化报告"""
        self.updates = []  # 更新的条目
        self.format_changes = []  # 格式变更
        self.dead_links = []  # 失效链接
        self.errors = []  # 错误信息
    
    def add_update(self, entry_id, old_type, new_type, changes):
        """添加更新记录"""
        self.updates.append({
            'entry_id': entry_id,
            'old_type': old_type,
            'new_type': new_type,
            'changes': changes
        })
    
    def add_format_change(self, entry_id, field, old_value, new_value):
        """添加格式变更记录"""
        self.format_changes.append({
            'entry_id': entry_id,
            'field': field,
            'old_value': old_value,
            'new_value': new_value
        })
    
    def add_dead_link(self, entry_id, field, url, status):
        """添加失效链接记录"""
        self.dead_links.append({
            'entry_id': entry_id,
            'field': field,
            'url': url,
            'status': status
        })
    
    def add_error(self, entry_id, message):
        """添加错误信息"""
        self.errors.append({
            'entry_id': entry_id,
            'message': message
        })
    
    def print_report(self):
        """打印报告"""
        
        # 打印更新信息
        if self.updates:
            print(f"\n{Fore.GREEN}[更新] 成功更新 {len(self.updates)} 个条目:{Style.RESET_ALL}")
            for update in self.updates:
                print(f"  - {Fore.CYAN}{update['entry_id']}{Style.RESET_ALL}: "
                      f"{update['old_type']} → {update['new_type']}")
                for field, (old, new) in update['changes'].items():
                    if old != new:
                        print(f"    • {field}: {old[:50]}... → {new[:50]}...")
        else:
            print(f"\n{Fore.YELLOW}[更新] 没有需要更新的条目{Style.RESET_ALL}")
        
        # 打印格式变更
        if self.format_changes:
            print(f"\n{Fore.GREEN}[格式] 统一了 {len(self.format_changes)} 处格式:{Style.RESET_ALL}")
            for change in self.format_changes:
                print(f"  - {Fore.CYAN}{change['entry_id']}{Style.RESET_ALL}.{change['field']}: "
                      f"{change['old_value']} → {change['new_value']}")
        else:
            print(f"\n{Fore.YELLOW}[格式] 没有需要统一的格式{Style.RESET_ALL}")
        
        # 打印失效链接
        if self.dead_links:
            print(f"\n{Fore.RED}[链接] 发现 {len(self.dead_links)} 个失效链接:{Style.RESET_ALL}")
            for link in self.dead_links:
                print(f"  - {Fore.CYAN}{link['entry_id']}{Style.RESET_ALL}.{link['field']}: "
                      f"{link['url']}")
                print(f"    状态: {link['status']}")
        else:
            print(f"\n{Fore.GREEN}[链接] 所有链接都可访问{Style.RESET_ALL}")
        
        # 打印错误信息
        if self.errors:
            print(f"\n{Fore.RED}[错误] 处理过程中出现 {len(self.errors)} 个错误:{Style.RESET_ALL}")
            for error in self.errors:
                print(f"  - {Fore.CYAN}{error['entry_id']}{Style.RESET_ALL}: {error['message']}")
        
        # 统计信息
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}统计信息:{Style.RESET_ALL}")
        print(f"  • 更新条目: {len(self.updates)}")
        print(f"  • 格式变更: {len(self.format_changes)}")
        print(f"  • 失效链接: {len(self.dead_links)}")
        print(f"  • 错误: {len(self.errors)}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'updates': self.updates,
            'format_changes': self.format_changes,
            'dead_links': self.dead_links,
            'errors': self.errors
        }
