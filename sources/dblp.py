"""DBLP API 适配器"""

import requests
import time
import xml.etree.ElementTree as ET


class DBLPAPI:
    """DBLP API 客户端"""
    
    def __init__(self, config):
        """初始化"""
        self.config = config.get('sources', {}).get('dblp', {})
        self.base_url = self.config.get('base_url', 'https://dblp.org/search/publ/api')
        self.timeout = self.config.get('timeout', 10)
        self.retry = self.config.get('retry', 3)
        self.session = requests.Session()
    
    def search_paper(self, title=None, arxiv_id=None):
        """搜索论文"""
        if arxiv_id:
            # DBLP 也索引了 arXiv 论文
            arxiv_id = arxiv_id.replace('arXiv:', '').strip()
            return self._search(f"arxiv:{arxiv_id}")
        elif title:
            return self._search(title)
        return None
    
    def _search(self, query):
        """执行搜索"""
        params = {
            'q': query,
            'h': 1,  # 只返回第一个结果
            'format': 'xml'
        }
        
        for attempt in range(self.retry):
            try:
                response = self.session.get(self.base_url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    return self._parse_result(response.text)
                elif response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return None
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"DBLP API 错误: {e}")
                    return None
                time.sleep(1)
        
        return None
    
    def _parse_result(self, xml_text):
        """解析 XML 结果"""
        try:
            root = ET.fromstring(xml_text)
            
            # 查找第一个 hit
            hit = root.find('.//hit')
            if hit is None:
                return None
            
            info = hit.find('info')
            if info is None:
                return None
            
            # 提取信息
            title = info.find('title')
            authors = info.findall('author')
            year = info.find('year')
            venue = info.find('venue')
            doi = info.find('doi')
            pub_type = info.find('type')
            
            # 判断是否是正式出版（不是 arXiv only）
            venue_text = venue.text if venue is not None else ''
            type_text = pub_type.text if pub_type is not None else ''
            
            # 如果是 arXiv only，不返回
            if 'arxiv' in venue_text.lower() and not doi:
                return None
            
            # 判断出版类型
            is_conference = type_text in ['Conference and Workshop Papers', 'Conference Paper']
            is_journal = type_text in ['Journal Articles', 'Journal Article']
            
            if not (is_conference or is_journal):
                return None
            
            result = {
                'title': title.text if title is not None else '',
                'authors': [author.text for author in authors],
                'year': year.text if year is not None else '',
                'venue': venue_text,
                'doi': doi.text if doi is not None else '',
                'publication_type': 'conference' if is_conference else 'journal',
                'is_published': True
            }
            
            return result
        except Exception as e:
            print(f"DBLP XML 解析错误: {e}")
            return None
