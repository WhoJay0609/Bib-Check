"""自动修复常见字段问题"""

import re


class AutoFixer:
    """自动修复器"""

    def __init__(self, config, report):
        self.config = config.get('auto_fix', {})
        self.report = report
        self.fix_doi = self.config.get('fix_doi', True)
        self.fix_url = self.config.get('fix_url', True)
        self.fix_pages = self.config.get('fix_pages', True)
        self.fix_year = self.config.get('fix_year', True)
        self.fix_whitespace = self.config.get('fix_whitespace', True)

    def fix_entries(self, bib_database, apply=True):
        changed = False
        for entry in bib_database.entries:
            if self._fix_entry(entry, apply):
                changed = True
        return changed

    def _fix_entry(self, entry, apply):
        entry_id = entry.get('ID', 'unknown')
        updated = False

        def record_fix(field, old_value, new_value, reason):
            nonlocal updated
            if old_value == new_value:
                return
            updated = True
            if apply:
                entry[field] = new_value
            self.report.add_fix(entry_id, field, old_value, new_value, reason)

        for field in list(entry.keys()):
            value = entry.get(field)
            if value is None:
                continue
            if self.fix_whitespace and isinstance(value, str):
                trimmed = value.strip()
                if trimmed != value:
                    record_fix(field, value, trimmed, "去除首尾空格")

        if self.fix_doi and 'doi' in entry:
            value = entry.get('doi', '')
            normalized = self._normalize_doi(value)
            if normalized and normalized != value:
                record_fix('doi', value, normalized, "规范化 DOI")

        if self.fix_url:
            for field in ['url', 'pdf']:
                if field not in entry:
                    continue
                value = entry.get(field, '')
                normalized = self._normalize_url(value)
                if normalized and normalized != value:
                    record_fix(field, value, normalized, "规范化 URL")

        if self.fix_pages and 'pages' in entry:
            value = entry.get('pages', '')
            normalized = self._normalize_pages(value)
            if normalized and normalized != value:
                record_fix('pages', value, normalized, "规范化页码范围")

        if self.fix_year and ('year' in entry or 'date' in entry):
            field = 'year' if 'year' in entry else 'date'
            value = entry.get(field, '')
            normalized = self._normalize_year(value)
            if normalized and normalized != value:
                record_fix(field, value, normalized, "提取年份")

        return updated

    def _normalize_doi(self, value):
        if not value:
            return ''
        doi = value.strip().lower()
        doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
        doi = doi.replace('doi:', '').strip()
        return doi

    def _normalize_url(self, value):
        if not value:
            return ''
        url = value.strip()
        if url.startswith('doi.org/'):
            url = 'https://' + url
        if url.startswith('www.'):
            url = 'https://' + url
        if url.startswith('http://') or url.startswith('https://'):
            return url
        return url

    def _normalize_pages(self, value):
        if not value:
            return ''
        pages = value.strip()
        if '--' in pages:
            return pages
        return re.sub(r'(\d+)\s*-\s*(\d+)', r'\1--\2', pages)

    def _normalize_year(self, value):
        if not value:
            return ''
        match = re.search(r'(\d{4})', str(value))
        return match.group(1) if match else str(value)
