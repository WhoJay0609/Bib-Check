"""BibTeX 解析工具"""

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase


class BibParser:
    """BibTeX 解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.parser = BibTexParser(common_strings=True)
        self.parser.ignore_nonstandard_types = False
        self.parser.homogenize_fields = True
        
        self.writer = BibTexWriter()
        self.writer.indent = '  '
        self.writer.order_entries_by = None
    
    def parse_file(self, filepath):
        """解析 BibTeX 文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 如果是 .tex 文件，提取其中的 .bib 内容
            if filepath.endswith('.tex'):
                content = self._extract_bib_from_tex(content)
            
            bib_database = bibtexparser.loads(content, parser=self.parser)
            return bib_database
        except Exception as e:
            print(f"解析文件出错: {e}")
            return None
    
    def _extract_bib_from_tex(self, content):
        """从 .tex 文件中提取 BibTeX 内容"""
        # 简单实现：查找 \begin{thebibliography} 或直接返回
        # 在实际使用中，通常 .tex 文件引用 .bib 文件，而不是包含它
        # 这里假设用户会直接传入 .bib 文件
        return content
    
    def parse_string(self, content):
        """解析 BibTeX 字符串"""
        try:
            bib_database = bibtexparser.loads(content, parser=self.parser)
            return bib_database
        except Exception as e:
            print(f"解析字符串出错: {e}")
            return None
    
    def write_file(self, bib_database, filepath):
        """写入 BibTeX 文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.writer.write(bib_database))
            return True
        except Exception as e:
            print(f"写入文件出错: {e}")
            return False
    
    def to_string(self, bib_database):
        """转换为字符串"""
        return self.writer.write(bib_database)
