"""报告生成工具"""

import csv
import json
import threading
from urllib.parse import quote
from colorama import Fore, Style


class Report:
    """报告类"""
    
    def __init__(self):
        """初始化报告"""
        self._lock = threading.Lock()
        self.updates = []  # 更新的条目
        self.update_candidates = []  # 可更新的条目（已检索到正式版本）
        self.update_misses = []  # 未找到正式版本
        self.author_truncations = []  # 作者截断
        self.fixes = []  # 自动修复
        self.dead_links = []  # 失效链接
        self.errors = []  # 错误信息
        self.validation_issues = {  # 校验问题
            'missing_fields': [],
            'author_format': [],
            'journal_abbrev': [],
            'duplicate_ids': [],
            'type_issues': [],
            'doi_format': [],
            'isbn_format': [],
            'issn_format': [],
            'year_range': [],
            'pages_format': [],
            'url_format': []
        }
    
    def add_update(self, entry_id, old_type, new_type, changes):
        """添加更新记录"""
        with self._lock:
            self.updates.append({
                'entry_id': entry_id,
                'old_type': old_type,
                'new_type': new_type,
                'changes': changes
            })

    def add_update_candidate(self, entry_id, title, venue, year, doi, urls, sources, arxiv_id):
        """添加可更新条目记录"""
        with self._lock:
            self.update_candidates.append({
                'entry_id': entry_id,
                'title': title,
                'venue': venue,
                'year': year,
                'doi': doi,
                'urls': urls,
                'sources': sources,
                'arxiv_id': arxiv_id
            })

    def add_update_miss(self, entry_id, title, arxiv_id):
        """添加未找到正式版本记录"""
        with self._lock:
            self.update_misses.append({
                'entry_id': entry_id,
                'title': title,
                'arxiv_id': arxiv_id
            })
    
    def add_author_truncation(self, entry_id, old_value, new_value, total_authors, max_authors):
        """添加作者截断记录"""
        with self._lock:
            self.author_truncations.append({
                'entry_id': entry_id,
                'old_value': old_value,
                'new_value': new_value,
                'total_authors': total_authors,
                'max_authors': max_authors
            })

    def add_fix(self, entry_id, field, old_value, new_value, reason):
        """添加自动修复记录"""
        with self._lock:
            self.fixes.append({
                'entry_id': entry_id,
                'field': field,
                'old_value': old_value,
                'new_value': new_value,
                'reason': reason
            })
    
    def add_dead_link(self, entry_id, field, url, status):
        """添加失效链接记录"""
        with self._lock:
            self.dead_links.append({
                'entry_id': entry_id,
                'field': field,
                'url': url,
                'status': status
            })
    
    def add_error(self, entry_id, message):
        """添加错误信息"""
        with self._lock:
            self.errors.append({
                'entry_id': entry_id,
                'message': message
            })
    
    def add_validation_issue(self, issue_type, entry_id, message):
        """添加校验问题"""
        with self._lock:
            if issue_type not in self.validation_issues:
                self.validation_issues[issue_type] = []
            
            self.validation_issues[issue_type].append({
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
        
        # 打印作者截断
        if self.author_truncations:
            print(f"\n{Fore.GREEN}[作者] 截断了 {len(self.author_truncations)} 个条目:{Style.RESET_ALL}")
            for change in self.author_truncations:
                print(f"  - {Fore.CYAN}{change['entry_id']}{Style.RESET_ALL}: "
                      f"{change['old_value']} → {change['new_value']}")
        else:
            print(f"\n{Fore.YELLOW}[作者] 没有需要截断的作者{Style.RESET_ALL}")

        # 打印自动修复
        if self.fixes:
            print(f"\n{Fore.GREEN}[修复] 自动修复 {len(self.fixes)} 处问题:{Style.RESET_ALL}")
            for fix in self.fixes[:10]:
                print(f"  - {Fore.CYAN}{fix['entry_id']}{Style.RESET_ALL}: "
                      f"{fix['field']} {fix['old_value']} → {fix['new_value']}")
            if len(self.fixes) > 10:
                print(f"    ... 还有 {len(self.fixes) - 10} 个")
        else:
            print(f"\n{Fore.YELLOW}[修复] 没有自动修复项{Style.RESET_ALL}")
        
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
        
        # 打印校验问题
        total_validation_issues = sum(len(v) for v in self.validation_issues.values())
        if total_validation_issues > 0:
            print(f"\n{Fore.YELLOW}[校验] 发现 {total_validation_issues} 个校验问题:{Style.RESET_ALL}")
            
            if self.validation_issues['missing_fields']:
                print(f"  {Fore.YELLOW}• 缺失字段 ({len(self.validation_issues['missing_fields'])} 个):{Style.RESET_ALL}")
                for issue in self.validation_issues['missing_fields'][:5]:  # 只显示前5个
                    print(f"    - {Fore.CYAN}{issue['entry_id']}{Style.RESET_ALL}: {issue['message']}")
                if len(self.validation_issues['missing_fields']) > 5:
                    print(f"    ... 还有 {len(self.validation_issues['missing_fields']) - 5} 个")
            
            if self.validation_issues['author_format']:
                print(f"  {Fore.YELLOW}• 作者格式问题 ({len(self.validation_issues['author_format'])} 个):{Style.RESET_ALL}")
                for issue in self.validation_issues['author_format'][:5]:
                    print(f"    - {Fore.CYAN}{issue['entry_id']}{Style.RESET_ALL}: {issue['message']}")
                if len(self.validation_issues['author_format']) > 5:
                    print(f"    ... 还有 {len(self.validation_issues['author_format']) - 5} 个")
            
            if self.validation_issues['journal_abbrev']:
                print(f"  {Fore.YELLOW}• 期刊缩写 ({len(self.validation_issues['journal_abbrev'])} 个):{Style.RESET_ALL}")
                for issue in self.validation_issues['journal_abbrev'][:5]:
                    print(f"    - {Fore.CYAN}{issue['entry_id']}{Style.RESET_ALL}: {issue['message']}")
                if len(self.validation_issues['journal_abbrev']) > 5:
                    print(f"    ... 还有 {len(self.validation_issues['journal_abbrev']) - 5} 个")
            
            if self.validation_issues['duplicate_ids']:
                print(f"  {Fore.YELLOW}• 重复 ID ({len(self.validation_issues['duplicate_ids'])} 个):{Style.RESET_ALL}")
                for issue in self.validation_issues['duplicate_ids']:
                    print(f"    - {Fore.CYAN}{issue['entry_id']}{Style.RESET_ALL}: {issue['message']}")
            
            if self.validation_issues['type_issues']:
                print(f"  {Fore.YELLOW}• 类型问题 ({len(self.validation_issues['type_issues'])} 个):{Style.RESET_ALL}")
                for issue in self.validation_issues['type_issues']:
                    print(f"    - {Fore.CYAN}{issue['entry_id']}{Style.RESET_ALL}: {issue['message']}")
        
        # 统计信息
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}统计信息:{Style.RESET_ALL}")
        print(f"  • 更新条目: {len(self.updates)}")
        print(f"  • 可更新条目: {len(self.update_candidates)}")
        print(f"  • 未找到正式版本: {len(self.update_misses)}")
        print(f"  • 作者截断: {len(self.author_truncations)}")
        print(f"  • 自动修复: {len(self.fixes)}")
        print(f"  • 失效链接: {len(self.dead_links)}")
        print(f"  • 校验问题: {total_validation_issues}")
        print(f"  • 错误: {len(self.errors)}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'modifications': {
                'updates': self.updates,
                'author_truncations': self.author_truncations,
                'fixes': self.fixes
            },
            'issues': {
                'dead_links': self.dead_links,
                'errors': self.errors,
                'validation': self.validation_issues
            },
            'update_candidates': self.update_candidates,
            'update_misses': self.update_misses
        }

    def write_markdown(self, filepath):
        """写入 Markdown 报告"""
        try:
            lines = []
            lines.append("# Bib-Check 报告")
            lines.append("")
            lines.append("## 可更新条目（已检索到正式版本）")
            if self.update_candidates:
                lines.append("")
                lines.append("| entry_id | title | venue | year | doi | doi_link | arxiv_link | semantic_scholar_link | dblp_link |")
                lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
                for item in self.update_candidates:
                    doi = item.get('doi', '')
                    urls = item.get('urls', {}) or {}
                    arxiv_id = item.get('arxiv_id', '')
                    ss_link = urls.get('semantic-scholar', '')
                    dblp_link = urls.get('dblp', '')
                    if not dblp_link:
                        dblp_link = f"https://dblp.org/search?q={quote(item.get('title', ''))}"
                    doi_link = f"https://doi.org/{doi}" if doi else ''
                    arxiv_link = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ''
                    lines.append(
                        f"| {item.get('entry_id','')} | {item.get('title','')} | "
                        f"{item.get('venue','')} | {item.get('year','')} | {doi} | "
                        f"{doi_link} | {arxiv_link} | {ss_link} | {dblp_link} |"
                    )
            else:
                lines.append("")
                lines.append("- 无")

            lines.append("")
            lines.append("## 未检索到正式版本")
            if self.update_misses:
                for item in self.update_misses:
                    lines.append(
                        f"- {item.get('entry_id','')}: {item.get('title','')} "
                        f"(arXiv: {item.get('arxiv_id','')})"
                    )
            else:
                lines.append("- 无")

            lines.append("")
            lines.append("## 具体修改")
            if self.updates:
                for update in self.updates:
                    lines.append(f"- {update['entry_id']}: {update['old_type']} → {update['new_type']}")
                    for field, (old, new) in update['changes'].items():
                        lines.append(f"  - {field}: {old} → {new}")
            else:
                lines.append("- 无")

            lines.append("")
            lines.append("## 作者截断")
            if self.author_truncations:
                for change in self.author_truncations:
                    lines.append(
                        f"- {change['entry_id']}: {change['old_value']} → {change['new_value']}"
                    )
            else:
                lines.append("- 无")

            lines.append("")
            lines.append("## 自动修复")
            if self.fixes:
                for fix in self.fixes:
                    lines.append(
                        f"- {fix['entry_id']}: {fix['field']} "
                        f"{fix['old_value']} → {fix['new_value']} ({fix['reason']})"
                    )
            else:
                lines.append("- 无")

            lines.append("")
            lines.append("## 失效链接")
            if self.dead_links:
                for link in self.dead_links:
                    lines.append(
                        f"- {link['entry_id']}.{link['field']}: {link['url']} "
                        f"({link['status']})"
                    )
            else:
                lines.append("- 无")

            lines.append("")
            lines.append("## 错误")
            if self.errors:
                for error in self.errors:
                    lines.append(f"- {error['entry_id']}: {error['message']}")
            else:
                lines.append("- 无")
            
            # 校验问题
            lines.append("")
            lines.append("## 校验问题")
            total_validation = sum(len(v) for v in self.validation_issues.values())
            if total_validation > 0:
                if self.validation_issues['missing_fields']:
                    lines.append("")
                    lines.append("### 缺失字段")
                    for issue in self.validation_issues['missing_fields']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")
                
                if self.validation_issues['author_format']:
                    lines.append("")
                    lines.append("### 作者格式问题")
                    for issue in self.validation_issues['author_format']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")
                
                if self.validation_issues['journal_abbrev']:
                    lines.append("")
                    lines.append("### 期刊缩写")
                    for issue in self.validation_issues['journal_abbrev']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")
                
                if self.validation_issues['duplicate_ids']:
                    lines.append("")
                    lines.append("### 重复 ID")
                    for issue in self.validation_issues['duplicate_ids']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")
                
                if self.validation_issues['type_issues']:
                    lines.append("")
                    lines.append("### 类型问题")
                    for issue in self.validation_issues['type_issues']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")

                if self.validation_issues['doi_format']:
                    lines.append("")
                    lines.append("### DOI 格式")
                    for issue in self.validation_issues['doi_format']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")

                if self.validation_issues['isbn_format']:
                    lines.append("")
                    lines.append("### ISBN 格式")
                    for issue in self.validation_issues['isbn_format']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")

                if self.validation_issues['issn_format']:
                    lines.append("")
                    lines.append("### ISSN 格式")
                    for issue in self.validation_issues['issn_format']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")

                if self.validation_issues['year_range']:
                    lines.append("")
                    lines.append("### 年份范围")
                    for issue in self.validation_issues['year_range']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")

                if self.validation_issues['pages_format']:
                    lines.append("")
                    lines.append("### 页码格式")
                    for issue in self.validation_issues['pages_format']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")

                if self.validation_issues['url_format']:
                    lines.append("")
                    lines.append("### URL 格式")
                    for issue in self.validation_issues['url_format']:
                        lines.append(f"- {issue['entry_id']}: {issue['message']}")
            else:
                lines.append("- 无")

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines) + "\n")
            return True
        except Exception as e:
            print(f"{Fore.RED}[错误] 写入 Markdown 报告失败: {e}{Style.RESET_ALL}")
            return False

    def write_csv(self, filepath):
        """写入 CSV 报告"""
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['section', 'entry_id', 'field', 'message', 'old_value', 'new_value', 'extra'])

                for update in self.updates:
                    entry_id = update.get('entry_id', '')
                    for field, (old, new) in update.get('changes', {}).items():
                        writer.writerow(['update', entry_id, field, '', old, new, ''])

                for change in self.author_truncations:
                    writer.writerow([
                        'author_truncation',
                        change.get('entry_id', ''),
                        'author',
                        '',
                        change.get('old_value', ''),
                        change.get('new_value', ''),
                        ''
                    ])

                for fix in self.fixes:
                    writer.writerow([
                        'auto_fix',
                        fix.get('entry_id', ''),
                        fix.get('field', ''),
                        fix.get('reason', ''),
                        fix.get('old_value', ''),
                        fix.get('new_value', ''),
                        ''
                    ])

                for link in self.dead_links:
                    writer.writerow([
                        'dead_link',
                        link.get('entry_id', ''),
                        link.get('field', ''),
                        link.get('status', ''),
                        '',
                        '',
                        link.get('url', '')
                    ])

                for error in self.errors:
                    writer.writerow([
                        'error',
                        error.get('entry_id', ''),
                        '',
                        error.get('message', ''),
                        '',
                        '',
                        ''
                    ])

                for category, issues in self.validation_issues.items():
                    for issue in issues:
                        writer.writerow([
                            f"validation:{category}",
                            issue.get('entry_id', ''),
                            '',
                            issue.get('message', ''),
                            '',
                            '',
                            ''
                        ])
            return True
        except Exception as e:
            print(f"{Fore.RED}[错误] 写入 CSV 报告失败: {e}{Style.RESET_ALL}")
            return False

    def write_latex(self, filepath):
        """写入 LaTeX 报告"""
        try:
            lines = []
            lines.append("\\documentclass{article}")
            lines.append("\\usepackage[utf8]{inputenc}")
            lines.append("\\usepackage{geometry}")
            lines.append("\\geometry{margin=1in}")
            lines.append("\\begin{document}")
            lines.append("\\section*{Bib-Check 报告}")

            lines.append("\\subsection*{可更新条目}")
            if self.update_candidates:
                for item in self.update_candidates:
                    title = self._escape_latex(item.get('title', ''))
                    lines.append(f"\\textbf{{{self._escape_latex(item.get('entry_id',''))}}}: {title}\\\\")
            else:
                lines.append("无\\\\")

            lines.append("\\subsection*{未检索到正式版本}")
            if self.update_misses:
                for item in self.update_misses:
                    lines.append(self._escape_latex(item.get('title', '')) + "\\\\")
            else:
                lines.append("无\\\\")

            lines.append("\\subsection*{具体修改}")
            if self.updates:
                for update in self.updates:
                    lines.append(self._escape_latex(update.get('entry_id', '')) + "\\\\")
            else:
                lines.append("无\\\\")

            lines.append("\\subsection*{作者截断}")
            if self.author_truncations:
                for change in self.author_truncations:
                    lines.append(self._escape_latex(change.get('entry_id', '')) + "\\\\")
            else:
                lines.append("无\\\\")

            lines.append("\\subsection*{自动修复}")
            if self.fixes:
                for fix in self.fixes:
                    lines.append(self._escape_latex(fix.get('entry_id', '')) + "\\\\")
            else:
                lines.append("无\\\\")

            lines.append("\\subsection*{失效链接}")
            if self.dead_links:
                for link in self.dead_links:
                    lines.append(self._escape_latex(link.get('url', '')) + "\\\\")
            else:
                lines.append("无\\\\")

            lines.append("\\subsection*{校验问题}")
            total_validation = sum(len(v) for v in self.validation_issues.values())
            if total_validation > 0:
                for category, issues in self.validation_issues.items():
                    if not issues:
                        continue
                    lines.append(f"\\paragraph*{{{self._escape_latex(self._get_category_name(category))}}}")
                    for issue in issues:
                        lines.append(self._escape_latex(issue.get('message', '')) + "\\\\")
            else:
                lines.append("无\\\\")

            lines.append("\\end{document}")

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines) + "\n")
            return True
        except Exception as e:
            print(f"{Fore.RED}[错误] 写入 LaTeX 报告失败: {e}{Style.RESET_ALL}")
            return False

    def write_pdf(self, filepath):
        """写入 PDF 报告"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except Exception:
            print(f"{Fore.YELLOW}[警告] 未安装 reportlab，无法生成 PDF 报告{Style.RESET_ALL}")
            return False

        try:
            c = canvas.Canvas(filepath, pagesize=A4)
            width, height = A4
            x = 40
            y = height - 40
            line_height = 14

            def draw_line(text):
                nonlocal y
                if y < 60:
                    c.showPage()
                    y = height - 40
                c.drawString(x, y, text)
                y -= line_height

            draw_line("Bib-Check 报告")
            draw_line(f"更新条目: {len(self.updates)}")
            draw_line(f"可更新条目: {len(self.update_candidates)}")
            draw_line(f"未找到正式版本: {len(self.update_misses)}")
            draw_line(f"作者截断: {len(self.author_truncations)}")
            draw_line(f"自动修复: {len(self.fixes)}")
            draw_line(f"失效链接: {len(self.dead_links)}")
            total_validation = sum(len(v) for v in self.validation_issues.values())
            draw_line(f"校验问题: {total_validation}")
            draw_line(f"错误: {len(self.errors)}")

            draw_line("")
            draw_line("校验问题明细:")
            for category, issues in self.validation_issues.items():
                if not issues:
                    continue
                draw_line(f"- {self._get_category_name(category)}: {len(issues)}")

            c.save()
            return True
        except Exception as e:
            print(f"{Fore.RED}[错误] 写入 PDF 报告失败: {e}{Style.RESET_ALL}")
            return False

    def write_json(self, filepath):
        """写入 JSON 报告"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"{Fore.RED}[错误] 写入报告失败: {e}{Style.RESET_ALL}")
            return False
    
    def write_html(self, filepath, bib_file=''):
        """写入 HTML 交互报告"""
        try:
            # 统计信息
            total_validation = sum(len(v) for v in self.validation_issues.values())
            
            html_content = f"""<!doctype html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<title>Bib-Check 报告</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
    background: #f5f5f5;
}}

#header {{
    background: white;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

#header h1 {{
    margin: 0 0 10px 0;
    color: #333;
}}

#controls {{
    background: white;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

#search {{
    width: 100%;
    padding: 10px;
    font-size: 14pt;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-bottom: 10px;
}}

.filter-buttons {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}}

.filter-btn {{
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    background: #e0e0e0;
    transition: background 0.2s;
}}

.filter-btn:hover {{
    background: #d0d0d0;
}}

.filter-btn.active {{
    background: #4CAF50;
    color: white;
}}

.stats {{
    background: #fff3cd;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 20px;
    border-left: 4px solid #ffc107;
}}

.stats h2 {{
    margin-top: 0;
    font-size: 18px;
}}

.stats ul {{
    margin: 10px 0;
    padding-left: 20px;
}}

.problem {{
    background: white;
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 8px;
    border-left: 4px solid #ff9800;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

.problem.severity-high {{
    border-left-color: #f44336;
}}

.problem.severity-medium {{
    border-left-color: #ff9800;
}}

.problem.severity-low {{
    border-left-color: #ffeb3b;
}}

.problem.severity-info {{
    border-left-color: #2196F3;
}}

.problem h3 {{
    margin: 0 0 10px 0;
    font-size: 16px;
    color: #333;
}}

.problem .message {{
    color: #666;
    margin: 5px 0;
}}

.problem .category {{
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    background: #e0e0e0;
    margin-right: 10px;
}}

.hidden {{
    display: none !important;
}}
</style>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
$(document).ready(function() {{
    // 搜索功能
    $('#search').on('input', function() {{
        const query = $(this).val().toLowerCase();
        if (query === '') {{
            $('.problem').show();
        }} else {{
            $('.problem').each(function() {{
                const text = $(this).text().toLowerCase();
                if (text.includes(query)) {{
                    $(this).show();
                }} else {{
                    $(this).hide();
                }}
            }});
        }}
    }});
    
    // 过滤按钮
    $('.filter-btn').click(function() {{
        $(this).toggleClass('active');
        updateFilters();
    }});
    
    function updateFilters() {{
        const activeFilters = $('.filter-btn.active').map(function() {{
            return $(this).data('category');
        }}).get();
        
        if (activeFilters.length === 0) {{
            $('.problem').show();
        }} else {{
            $('.problem').each(function() {{
                const category = $(this).data('category');
                if (activeFilters.includes(category)) {{
                    $(this).show();
                }} else {{
                    $(this).hide();
                }}
            }});
        }}
    }}
}});
</script>
</head>
<body>

<div id="header">
    <h1>Bib-Check 校验报告</h1>
    <p><strong>文件:</strong> {bib_file}</p>
</div>

<div id="controls">
    <input type="text" id="search" placeholder="搜索条目 ID 或问题描述...">
    <div class="filter-buttons">
        <button class="filter-btn" data-category="missing_fields">缺失字段</button>
        <button class="filter-btn" data-category="author_format">作者格式</button>
        <button class="filter-btn" data-category="journal_abbrev">期刊缩写</button>
        <button class="filter-btn" data-category="duplicate_ids">重复ID</button>
        <button class="filter-btn" data-category="type_issues">类型问题</button>
        <button class="filter-btn" data-category="doi_format">DOI 格式</button>
        <button class="filter-btn" data-category="isbn_format">ISBN 格式</button>
        <button class="filter-btn" data-category="issn_format">ISSN 格式</button>
        <button class="filter-btn" data-category="year_range">年份范围</button>
        <button class="filter-btn" data-category="pages_format">页码格式</button>
        <button class="filter-btn" data-category="url_format">URL 格式</button>
        <button class="filter-btn" data-category="dead_links">失效链接</button>
        <button class="filter-btn" data-category="auto_fixes">自动修复</button>
    </div>
</div>

<div class="stats">
    <h2>统计信息</h2>
    <ul>
        <li>更新条目: {len(self.updates)}</li>
        <li>可更新条目: {len(self.update_candidates)}</li>
        <li>未找到正式版本: {len(self.update_misses)}</li>
        <li>作者截断: {len(self.author_truncations)}</li>
        <li>自动修复: {len(self.fixes)}</li>
        <li>失效链接: {len(self.dead_links)}</li>
        <li>校验问题: {total_validation}</li>
        <li>错误: {len(self.errors)}</li>
    </ul>
</div>

<div id="problems">
"""
            
            # 添加校验问题
            problem_counter = 0
            
            for category, issues in self.validation_issues.items():
                for issue in issues:
                    problem_counter += 1
                    severity = self._get_severity(category)
                    category_name = self._get_category_name(category)
                    html_content += f"""
    <div class="problem severity-{severity}" data-category="{category}">
        <h3>#{problem_counter} - {issue['entry_id']}</h3>
        <span class="category">{category_name}</span>
        <div class="message">{self._escape_html(issue['message'])}</div>
    </div>
"""
            
            # 添加失效链接
            for link in self.dead_links:
                problem_counter += 1
                html_content += f"""
    <div class="problem severity-medium" data-category="dead_links">
        <h3>#{problem_counter} - {link['entry_id']}</h3>
        <span class="category">失效链接</span>
        <div class="message">字段: {link['field']}</div>
        <div class="message">URL: {self._escape_html(link['url'])}</div>
        <div class="message">状态: {self._escape_html(link['status'])}</div>
    </div>
"""

            # 添加自动修复
            for fix in self.fixes:
                problem_counter += 1
                html_content += f"""
    <div class="problem severity-info" data-category="auto_fixes">
        <h3>#{problem_counter} - {fix['entry_id']}</h3>
        <span class="category">自动修复</span>
        <div class="message">字段: {self._escape_html(fix['field'])}</div>
        <div class="message">变更: {self._escape_html(str(fix['old_value']))} → {self._escape_html(str(fix['new_value']))}</div>
        <div class="message">原因: {self._escape_html(fix['reason'])}</div>
    </div>
"""
            
            if problem_counter == 0:
                html_content += """
    <div class="problem severity-info" data-category="none">
        <h3>✓ 没有发现问题</h3>
        <div class="message">所有条目均通过校验</div>
    </div>
"""
            
            html_content += """
</div>

</body>
</html>"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            print(f"{Fore.RED}[错误] 写入 HTML 报告失败: {e}{Style.RESET_ALL}")
            return False
    
    def _get_severity(self, category):
        """获取问题严重性"""
        severity_map = {
            'missing_fields': 'high',
            'duplicate_ids': 'high',
            'author_format': 'medium',
            'type_issues': 'medium',
            'journal_abbrev': 'low',
            'doi_format': 'medium',
            'isbn_format': 'medium',
            'issn_format': 'medium',
            'year_range': 'medium',
            'pages_format': 'low',
            'url_format': 'low'
        }
        return severity_map.get(category, 'info')
    
    def _get_category_name(self, category):
        """获取分类名称"""
        name_map = {
            'missing_fields': '缺失字段',
            'author_format': '作者格式',
            'journal_abbrev': '期刊缩写',
            'duplicate_ids': '重复ID',
            'type_issues': '类型问题',
            'doi_format': 'DOI 格式',
            'isbn_format': 'ISBN 格式',
            'issn_format': 'ISSN 格式',
            'year_range': '年份范围',
            'pages_format': '页码格式',
            'url_format': 'URL 格式'
        }
        return name_map.get(category, category)
    
    def _escape_html(self, text):
        """转义 HTML"""
        if not text:
            return ''
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

    def _escape_latex(self, text):
        """转义 LaTeX"""
        if not text:
            return ''
        value = str(text)
        replacements = {
            '\\': r'\\textbackslash{}',
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}'
        }
        for src, dst in replacements.items():
            value = value.replace(src, dst)
        return value


class SummaryReport:
    """批量处理汇总报告"""

    def __init__(self, items):
        self.items = items

    def to_dict(self):
        total = {
            'updates': 0,
            'update_candidates': 0,
            'update_misses': 0,
            'author_truncations': 0,
            'fixes': 0,
            'dead_links': 0,
            'validation_issues': 0,
            'errors': 0
        }
        for item in self.items:
            stats = item.get('stats', {})
            for key in total:
                total[key] += int(stats.get(key, 0))
        return {
            'files': self.items,
            'total': total
        }

    def write_json(self, filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"{Fore.RED}[错误] 写入汇总报告失败: {e}{Style.RESET_ALL}")
            return False

    def write_markdown(self, filepath):
        try:
            lines = []
            lines.append("# Bib-Check 汇总报告")
            lines.append("")
            lines.append("| file | updates | update_candidates | update_misses | author_truncations | fixes | dead_links | validation_issues | errors |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
            for item in self.items:
                stats = item.get('stats', {})
                lines.append(
                    f"| {item.get('file','')} | {stats.get('updates',0)} | "
                    f"{stats.get('update_candidates',0)} | {stats.get('update_misses',0)} | "
                    f"{stats.get('author_truncations',0)} | {stats.get('fixes',0)} | "
                    f"{stats.get('dead_links',0)} | {stats.get('validation_issues',0)} | "
                    f"{stats.get('errors',0)} |"
                )

            total = self.to_dict().get('total', {})
            lines.append("")
            lines.append("## 总计")
            for key, value in total.items():
                lines.append(f"- {key}: {value}")

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines) + "\n")
            return True
        except Exception as e:
            print(f"{Fore.RED}[错误] 写入汇总报告失败: {e}{Style.RESET_ALL}")
            return False