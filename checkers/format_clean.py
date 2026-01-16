"""统一会议名称格式"""

import re
from colorama import Fore, Style
from tqdm import tqdm


class FormatCleaner:
    """格式清理器"""
    
    def __init__(self, config, report):
        """初始化"""
        self.config = config
        self.report = report
        self.venue_mappings = config.get('venue_mappings', [])
    
    def clean_entries(self, bib_database):
        """清理条目"""
        if not self.venue_mappings:
            print(f"{Fore.YELLOW}[信息] 没有配置会议名称映射规则{Style.RESET_ALL}")
            return bib_database
        
        print(f"{Fore.GREEN}[信息] 开始统一会议名称格式{Style.RESET_ALL}")
        
        # 遍历处理
        changed_count = 0
        for entry in tqdm(bib_database.entries, desc="处理条目", unit="条目"):
            if self._clean_entry(entry):
                changed_count += 1
        
        print(f"{Fore.GREEN}[成功] 成功统一 {changed_count} 个条目的格式{Style.RESET_ALL}")
        
        return bib_database
    
    def _clean_entry(self, entry):
        """清理单个条目"""
        changed = False
        
        # 检查需要清理的字段
        for field in ['booktitle', 'journal', 'venue']:
            if field in entry:
                old_value = entry[field]
                new_value = self._standardize_venue(old_value)
                
                if new_value and new_value != old_value:
                    entry[field] = new_value
                    self.report.add_format_change(
                        entry.get('ID', 'unknown'),
                        field,
                        old_value,
                        new_value
                    )
                    changed = True
        
        return changed
    
    def _standardize_venue(self, venue):
        """标准化会议名称"""
        if not venue:
            return venue
        
        # 移除大括号
        venue_clean = venue.replace('{', '').replace('}', '').strip()
        
        # 遍历映射规则
        for mapping in self.venue_mappings:
            patterns = mapping.get('patterns', [])
            standard = mapping.get('standard', '')
            
            for pattern in patterns:
                # 尝试精确匹配
                if venue_clean == pattern:
                    return standard
                
                # 尝试正则匹配
                try:
                    if re.search(pattern, venue_clean, re.IGNORECASE):
                        return standard
                except re.error:
                    # 不是有效的正则表达式，跳过
                    continue
        
        return venue
