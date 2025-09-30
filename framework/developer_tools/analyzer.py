"""
Log Analyzer Module

Provides advanced log analysis, pattern detection, and error tracking
for enhanced debugging and system monitoring.
"""

import re
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Pattern, Set, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Represents a log entry"""
    timestamp: datetime
    level: str
    message: str
    logger_name: str
    module: str
    function: str
    line_number: int
    thread_id: str
    process_id: str
    extra_data: Dict[str, Any]


@dataclass
class LogPattern:
    """Represents a detected log pattern"""
    pattern_id: str
    regex: str
    description: str
    severity: str
    count: int
    first_seen: datetime
    last_seen: datetime
    examples: List[str]


@dataclass
class ErrorAnalysis:
    """Error analysis results"""
    error_type: str
    count: int
    frequency: float
    first_occurrence: datetime
    last_occurrence: datetime
    affected_modules: List[str]
    stack_traces: List[str]
    potential_causes: List[str]
    recommendations: List[str]


class LogAnalyzer:
    """Advanced log analysis and pattern detection"""
    
    def __init__(self):
        self._log_entries: List[LogEntry] = []
        self._patterns: Dict[str, LogPattern] = {}
        self._error_signatures: Dict[str, List[LogEntry]] = defaultdict(list)
        self._compiled_patterns: Dict[str, Pattern] = {}
        self._setup_default_patterns()
    
    def add_log_entry(self, entry: LogEntry):
        """Add a log entry for analysis"""
        self._log_entries.append(entry)
        self._analyze_entry(entry)
    
    def parse_log_line(self, line: str, format_pattern: Optional[str] = None) -> Optional[LogEntry]:
        """Parse a log line into a LogEntry"""
        if format_pattern is None:
            # Default Python logging format
            format_pattern = r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (?P<logger_name>\S+) - (?P<level>\w+) - (?P<message>.*)'
        
        match = re.match(format_pattern, line)
        if match:
            try:
                timestamp = datetime.strptime(match.group('timestamp'), '%Y-%m-%d %H:%M:%S,%f')
                return LogEntry(
                    timestamp=timestamp,
                    level=match.group('level'),
                    message=match.group('message'),
                    logger_name=match.group('logger_name'),
                    module=match.groupdict().get('module', ''),
                    function=match.groupdict().get('function', ''),
                    line_number=int(match.groupdict().get('line_number', 0)),
                    thread_id=match.groupdict().get('thread_id', ''),
                    process_id=match.groupdict().get('process_id', ''),
                    extra_data={}
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse log line: {e}")
                return None
        return None
    
    def analyze_log_file(self, file_path: str, format_pattern: Optional[str] = None) -> Dict[str, Any]:
        """Analyze an entire log file"""
        entries_processed = 0
        errors_found = 0
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    entry = self.parse_log_line(line.strip(), format_pattern)
                    if entry:
                        self.add_log_entry(entry)
                        entries_processed += 1
                        if entry.level.upper() in ['ERROR', 'CRITICAL']:
                            errors_found += 1
        except Exception as e:
            logger.error(f"Error analyzing log file {file_path}: {e}")
        
        return {
            'file_path': file_path,
            'entries_processed': entries_processed,
            'errors_found': errors_found,
            'analysis': self.get_analysis_summary()
        }
    
    def detect_patterns(self, min_occurrences: int = 3) -> List[LogPattern]:
        """Detect recurring patterns in logs"""
        message_groups = defaultdict(list)
        
        # Group similar messages
        for entry in self._log_entries:
            # Normalize message by removing variable parts
            normalized = self._normalize_message(entry.message)
            message_groups[normalized].append(entry)
        
        patterns = []
        for normalized_msg, entries in message_groups.items():
            if len(entries) >= min_occurrences:
                pattern_id = f"pattern_{len(patterns) + 1}"
                pattern = LogPattern(
                    pattern_id=pattern_id,
                    regex=self._create_regex_from_message(normalized_msg),
                    description=f"Recurring pattern: {normalized_msg[:100]}",
                    severity=self._determine_pattern_severity(entries),
                    count=len(entries),
                    first_seen=min(e.timestamp for e in entries),
                    last_seen=max(e.timestamp for e in entries),
                    examples=[e.message for e in entries[:5]]
                )
                patterns.append(pattern)
                self._patterns[pattern_id] = pattern
        
        return patterns
    
    def analyze_errors(self) -> List[ErrorAnalysis]:
        """Analyze error patterns and trends"""
        error_entries = [e for e in self._log_entries if e.level.upper() in ['ERROR', 'CRITICAL']]
        error_groups = defaultdict(list)
        
        # Group errors by type/signature
        for entry in error_entries:
            signature = self._extract_error_signature(entry.message)
            error_groups[signature].append(entry)
        
        analyses = []
        for signature, entries in error_groups.items():
            if len(entries) >= 2:  # Only analyze recurring errors
                duration = (max(e.timestamp for e in entries) - min(e.timestamp for e in entries)).total_seconds()
                frequency = len(entries) / max(duration / 3600, 1)  # errors per hour
                
                analysis = ErrorAnalysis(
                    error_type=signature,
                    count=len(entries),
                    frequency=frequency,
                    first_occurrence=min(e.timestamp for e in entries),
                    last_occurrence=max(e.timestamp for e in entries),
                    affected_modules=list(set(e.module for e in entries if e.module)),
                    stack_traces=[e.message for e in entries if 'Traceback' in e.message],
                    potential_causes=self._analyze_potential_causes(entries),
                    recommendations=self._generate_recommendations(signature, entries)
                )
                analyses.append(analysis)
        
        return analyses
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get comprehensive analysis summary"""
        if not self._log_entries:
            return {}
        
        level_counts = Counter(e.level for e in self._log_entries)
        module_counts = Counter(e.module for e in self._log_entries if e.module)
        
        # Time-based analysis
        start_time = min(e.timestamp for e in self._log_entries)
        end_time = max(e.timestamp for e in self._log_entries)
        duration = (end_time - start_time).total_seconds()
        
        # Error rate calculation
        error_count = level_counts.get('ERROR', 0) + level_counts.get('CRITICAL', 0)
        error_rate = error_count / len(self._log_entries) * 100
        
        return {
            'total_entries': len(self._log_entries),
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_hours': duration / 3600
            },
            'level_distribution': dict(level_counts),
            'error_rate_percentage': error_rate,
            'top_modules': dict(module_counts.most_common(10)),
            'patterns_detected': len(self._patterns),
            'error_types': len(self._error_signatures)
        }
    
    def search_logs(self, query: str, level: Optional[str] = None, 
                   start_time: Optional[datetime] = None, 
                   end_time: Optional[datetime] = None) -> List[LogEntry]:
        """Search logs with filters"""
        results = []
        query_pattern = re.compile(query, re.IGNORECASE)
        
        for entry in self._log_entries:
            # Apply filters
            if level and entry.level.upper() != level.upper():
                continue
            
            if start_time and entry.timestamp < start_time:
                continue
            
            if end_time and entry.timestamp > end_time:
                continue
            
            # Check if query matches
            if query_pattern.search(entry.message):
                results.append(entry)
        
        return results
    
    def _setup_default_patterns(self):
        """Setup default error patterns"""
        self._compiled_patterns = {
            'connection_error': re.compile(r'connection.*(?:refused|timeout|failed)', re.IGNORECASE),
            'memory_error': re.compile(r'memory.*(?:error|out of memory|allocation failed)', re.IGNORECASE),
            'permission_error': re.compile(r'permission.*denied|access.*denied', re.IGNORECASE),
            'file_not_found': re.compile(r'file.*not found|no such file', re.IGNORECASE),
            'timeout_error': re.compile(r'timeout|timed out', re.IGNORECASE),
            'authentication_error': re.compile(r'auth.*(?:failed|error)|invalid.*credentials', re.IGNORECASE)
        }
    
    def _analyze_entry(self, entry: LogEntry):
        """Analyze individual log entry"""
        # Check against known error patterns
        if entry.level.upper() in ['ERROR', 'CRITICAL']:
            for pattern_name, pattern in self._compiled_patterns.items():
                if pattern.search(entry.message):
                    self._error_signatures[pattern_name].append(entry)
    
    def _normalize_message(self, message: str) -> str:
        """Normalize log message by removing variable parts"""
        # Remove timestamps
        message = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '<TIMESTAMP>', message)
        
        # Remove IP addresses
        message = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '<IP>', message)
        
        # Remove UUIDs
        message = re.sub(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', '<UUID>', message)
        
        # Remove numbers
        message = re.sub(r'\b\d+\b', '<NUM>', message)
        
        # Remove file paths
        message = re.sub(r'/[^\s]*', '<PATH>', message)
        
        return message
    
    def _create_regex_from_message(self, normalized_msg: str) -> str:
        """Create regex pattern from normalized message"""
        # Escape special regex characters
        escaped = re.escape(normalized_msg)
        
        # Replace placeholders with appropriate regex
        escaped = escaped.replace(r'\<TIMESTAMP\>', r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
        escaped = escaped.replace(r'\<IP\>', r'(?:\d{1,3}\.){3}\d{1,3}')
        escaped = escaped.replace(r'\<UUID\>', r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
        escaped = escaped.replace(r'\<NUM\>', r'\d+')
        escaped = escaped.replace(r'\<PATH\>', r'/[^\s]*')
        
        return escaped
    
    def _determine_pattern_severity(self, entries: List[LogEntry]) -> str:
        """Determine severity of a pattern based on log levels"""
        levels = [e.level.upper() for e in entries]
        
        if 'CRITICAL' in levels:
            return 'critical'
        elif 'ERROR' in levels:
            return 'error'
        elif 'WARNING' in levels:
            return 'warning'
        else:
            return 'info'
    
    def _extract_error_signature(self, message: str) -> str:
        """Extract error signature from message"""
        # Look for exception types
        exception_match = re.search(r'(\w+Error|\w+Exception)', message)
        if exception_match:
            return exception_match.group(1)
        
        # Look for common error patterns
        for pattern_name, pattern in self._compiled_patterns.items():
            if pattern.search(message):
                return pattern_name
        
        # Fallback to first few words
        words = message.split()[:3]
        return ' '.join(words)
    
    def _analyze_potential_causes(self, entries: List[LogEntry]) -> List[str]:
        """Analyze potential causes of errors"""
        causes = []
        
        # Check for common patterns in error messages
        messages = [e.message for e in entries]
        
        if any('connection' in msg.lower() for msg in messages):
            causes.append("Network connectivity issues")
        
        if any('memory' in msg.lower() for msg in messages):
            causes.append("Memory exhaustion or allocation issues")
        
        if any('permission' in msg.lower() or 'access' in msg.lower() for msg in messages):
            causes.append("Insufficient permissions or access rights")
        
        if any('timeout' in msg.lower() for msg in messages):
            causes.append("Resource contention or slow operations")
        
        return causes or ["Unknown cause - requires further investigation"]
    
    def _generate_recommendations(self, signature: str, entries: List[LogEntry]) -> List[str]:
        """Generate recommendations based on error analysis"""
        recommendations = []
        
        if 'connection' in signature.lower():
            recommendations.extend([
                "Check network connectivity and firewall settings",
                "Verify service availability and health",
                "Consider implementing connection retry logic"
            ])
        
        elif 'memory' in signature.lower():
            recommendations.extend([
                "Monitor memory usage and identify memory leaks",
                "Optimize data structures and algorithms",
                "Consider increasing available memory"
            ])
        
        elif 'permission' in signature.lower():
            recommendations.extend([
                "Review and update file/directory permissions",
                "Check user account privileges",
                "Verify service account configuration"
            ])
        
        elif 'timeout' in signature.lower():
            recommendations.extend([
                "Increase timeout values if appropriate",
                "Optimize slow operations and queries",
                "Consider asynchronous processing"
            ])
        
        else:
            recommendations.extend([
                "Review error details and stack traces",
                "Check application configuration",
                "Monitor system resources and dependencies"
            ])
        
        return recommendations


class ErrorTracker:
    """Tracks and manages error occurrences"""
    
    def __init__(self):
        self._errors: List[Dict[str, Any]] = []
        self._error_counts: Counter = Counter()
        self._resolved_errors: Set[str] = set()
    
    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track an error occurrence"""
        error_data = {
            'type': type(error).__name__,
            'message': str(error),
            'timestamp': datetime.now(),
            'context': context or {},
            'stack_trace': traceback.format_exc() if hasattr(traceback, 'format_exc') else str(error)
        }
        
        self._errors.append(error_data)
        self._error_counts[error_data['type']] += 1
        
        logger.error(f"Tracked error: {error_data['type']} - {error_data['message']}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error tracking summary"""
        if not self._errors:
            return {}
        
        recent_errors = [e for e in self._errors if e['timestamp'] > datetime.now() - timedelta(hours=24)]
        
        return {
            'total_errors': len(self._errors),
            'recent_errors_24h': len(recent_errors),
            'error_types': dict(self._error_counts.most_common()),
            'resolution_rate': len(self._resolved_errors) / len(self._errors) * 100 if self._errors else 0
        }
    
    def mark_resolved(self, error_signature: str):
        """Mark an error type as resolved"""
        self._resolved_errors.add(error_signature)


class PerformanceAnalyzer:
    """Analyzes performance metrics from logs"""
    
    def __init__(self):
        self._performance_data: List[Dict[str, Any]] = []
    
    def analyze_response_times(self, log_entries: List[LogEntry]) -> Dict[str, Any]:
        """Analyze response times from log entries"""
        response_times = []
        
        for entry in log_entries:
            # Look for response time patterns
            time_match = re.search(r'(\d+(?:\.\d+)?)\s*ms', entry.message)
            if time_match:
                response_times.append(float(time_match.group(1)))
        
        if not response_times:
            return {}
        
        return {
            'total_requests': len(response_times),
            'average_response_time': sum(response_times) / len(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'p95_response_time': self._percentile(response_times, 95),
            'p99_response_time': self._percentile(response_times, 99)
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        sorted_data = sorted(data)
        index = int(percentile / 100 * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


# Global instances
_log_analyzer = LogAnalyzer()
_error_tracker = ErrorTracker()
_performance_analyzer = PerformanceAnalyzer()

# Convenience functions
def analyze_log_file(file_path: str) -> Dict[str, Any]:
    """Analyze a log file"""
    return _log_analyzer.analyze_log_file(file_path)

def detect_log_patterns() -> List[LogPattern]:
    """Detect patterns in logs"""
    return _log_analyzer.detect_patterns()

def track_error(error: Exception, context: Dict[str, Any] = None):
    """Track an error"""
    _error_tracker.track_error(error, context)

def get_error_summary() -> Dict[str, Any]:
    """Get error summary"""
    return _error_tracker.get_error_summary()

# Import traceback for error tracking
import traceback