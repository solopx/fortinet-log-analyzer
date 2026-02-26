import re
import os
import csv
import json
import logging
from collections import Counter
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


@dataclass
class FilterCriteria:
    field_filters: Dict[str, str]
    free_text: str
    date_start: Optional[datetime]
    date_end: Optional[datetime]


class LogEngine:
    LOG_PATTERN = re.compile(r'(\w+)=((?:".*?")|\S+)')
    DATE_FORMATS = ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y')
    _HOUR_FMT   = '%Y-%m-%d %H:00'

    def __init__(self):
        self.all_logs: List[Dict[str, str]] = []
        self.filtered_logs: List[Dict[str, str]] = []
        self.columns: List[str] = []

    def parse_line(self, line: str) -> Dict[str, str]:
        parsed = {}
        for key, value in self.LOG_PATTERN.findall(line):
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            parsed[key] = value
        return parsed

    def load_file(self, filepath: str) -> Tuple[int, int]:
        self.all_logs.clear()
        all_keys = set()
        size = os.path.getsize(filepath)

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.replace('\x00', '').strip()
                if not line:
                    continue
                data = self.parse_line(line)
                self.all_logs.append(data)
                all_keys.update(data.keys())

        priority = ['date', 'time', 'user', 'srcip', 'dstip',
                    'action', 'status', 'level', 'msg']
        self.columns = [c for c in priority if c in all_keys]
        self.columns += [c for c in sorted(all_keys) if c not in self.columns]

        return len(self.all_logs), size

    def parse_query(self, query: str) -> Tuple[Dict[str, str], str]:
        filters = {}
        free_text_parts = []

        for part in query.split():
            if ':' in part and part.count(':') == 1:
                k, v = part.split(':', 1)
                if k.strip():
                    filters[k.lower().strip()] = v.lower().strip()
                else:
                    free_text_parts.append(part)
            else:
                free_text_parts.append(part)

        return filters, ' '.join(free_text_parts).strip()

    def parse_log_datetime(self, log: Dict[str, str]) -> Optional[datetime]:
        log_date = log.get('date', '').strip()
        log_time = log.get('time', '').strip()
        if not log_date or not log_time:
            return None

        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(f'{log_date} {log_time}',
                                         f'{fmt} %H:%M:%S')
            except ValueError:
                continue
        return None

    def apply_filter(self, criteria: FilterCriteria) -> int:
        self.filtered_logs.clear()

        for log in self.all_logs:
            if criteria.date_start or criteria.date_end:
                log_dt = self.parse_log_datetime(log)
                if log_dt is None:
                    continue
                if criteria.date_start and log_dt < criteria.date_start:
                    continue
                if criteria.date_end and log_dt > criteria.date_end:
                    continue

            if criteria.field_filters:
                match = all(
                    v in str(log.get(k, '')).lower()
                    for k, v in criteria.field_filters.items()
                )
                if not match:
                    continue

            if criteria.free_text:
                if not any(criteria.free_text.lower() in str(v).lower()
                           for v in log.values()):
                    continue

            self.filtered_logs.append(log)

        return len(self.filtered_logs)

    def get_page(self, page_num: int, page_size: int) -> List[Dict[str, str]]:
        start = page_num * page_size
        end = start + page_size
        return self.filtered_logs[start:end]

    def sort_logs(self, column: str, ascending: bool = True):
        try:
            self.filtered_logs.sort(
                key=lambda x: float(x.get(column, 0)),
                reverse=not ascending
            )
        except ValueError:
            self.filtered_logs.sort(
                key=lambda x: str(x.get(column, '')).lower(),
                reverse=not ascending
            )

    def get_statistics(self) -> Dict[str, Counter]:
        return {
            'actions': Counter(log.get('action', '-') for log in self.filtered_logs),
            'levels':  Counter(log.get('level',  '-') for log in self.filtered_logs),
            'srcips':  Counter(log.get('srcip',  '-') for log in self.filtered_logs),
            'dstips':  Counter(log.get('dstip',  '-') for log in self.filtered_logs),
        }

    def export_csv(self, filepath: str):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.columns)
            for log in self.filtered_logs:
                writer.writerow([log.get(c, '') for c in self.columns])

    def export_json(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.filtered_logs, f, indent=2)

    def get_timeline_data(self) -> Dict[str, int]:
        timeline = Counter()
        for log in self.filtered_logs:
            log_dt = self.parse_log_datetime(log)
            if log_dt:
                timeline[log_dt.strftime(self._HOUR_FMT)] += 1
        return dict(sorted(timeline.items()))

    def get_top_data(self, field: str, limit: int = 10) -> List[Tuple[str, int]]:
        counter = Counter(log.get(field, '-') for log in self.filtered_logs)
        return counter.most_common(limit)

    def get_30min_distribution(self) -> Dict[str, int]:
        intervals = Counter()
        for log in self.filtered_logs:
            log_dt = self.parse_log_datetime(log)
            if log_dt:
                minute_interval = '00-30' if log_dt.minute < 30 else '30-00'
                key = f'{log_dt.hour:02d}:{minute_interval}'
                intervals[key] += 1
        return dict(sorted(intervals.items()))

    def get_level_counts(self) -> Counter:
        return Counter(log.get('level', 'unknown') for log in self.filtered_logs)

    def get_error_time_series(self) -> Dict[str, int]:
        counter = Counter()
        for log in self.filtered_logs:
            level = log.get('level', '').lower()
            if level in ('error', 'critical', 'alert'):
                dt = self.parse_log_datetime(log)
                if dt:
                    counter[dt.strftime(self._HOUR_FMT)] += 1
        return dict(sorted(counter.items()))
