"""
Pre-parse filters to exclude jobs BEFORE LLM parsing.
Uses regex to scan raw text - no API calls.
"""

import re
import logging
from typing import Tuple, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PreFilterResult:
    passed: bool
    reason: Optional[str] = None
    details: Optional[str] = None


class PreParseFilter:
    """
    Filters job postings BEFORE LLM parsing to save API costs.
    
    Checks:
    1. Years of experience > max_yoe (default 5)
    2. Location outside US
    3. US citizenship / security clearance requirements
    """
    
    YOE_PATTERNS = [
        r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)',
        r'(\d+)\s*-\s*\d+\s*(?:years?|yrs?)',
        r'(?:minimum|at least|requires?)\s+(\d+)\s*(?:years?|yrs?)',
        r'(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant|professional|industry)',
    ]
    
    NON_US_LOCATIONS = [
        # Countries
        'india', 'uk', 'united kingdom', 'canada', 'germany', 'france',
        'singapore', 'australia', 'ireland', 'netherlands', 'israel',
        'japan', 'china', 'brazil', 'mexico', 'poland', 'romania',
        'philippines', 'vietnam', 'ukraine', 'spain', 'italy', 'sweden',
        # Non-US Cities
        'bangalore', 'bengaluru', 'hyderabad', 'pune', 'mumbai', 'delhi',
        'chennai', 'noida', 'gurgaon', 'gurugram',
        'london', 'manchester', 'edinburgh', 'cambridge uk',
        'toronto', 'vancouver', 'montreal', 'ottawa', 'calgary',
        'berlin', 'munich', 'frankfurt', 'hamburg',
        'paris', 'amsterdam', 'dublin', 'tel aviv',
        'tokyo', 'shanghai', 'beijing', 'sydney', 'melbourne',
    ]
    
    CITIZENSHIP_PATTERNS = [
        r'us\s+citizen(?:ship)?(?:\s+required)?',
        r'u\.s\.\s+citizen(?:ship)?',
        r'united\s+states\s+citizen',
        r'must\s+be\s+(?:a\s+)?(?:us|u\.s\.)\s+citizen',
        r'security\s+clearance\s+required',
        r'active\s+(?:security\s+)?clearance',
        r'(?:secret|top\s+secret|ts/sci)\s+clearance',
        r'able\s+to\s+obtain\s+(?:security\s+)?clearance',
        r'must\s+(?:be\s+able\s+to\s+)?(?:obtain|hold|maintain)\s+.*?clearance',
        r'(?:no|not|unable\s+to)\s+(?:provide\s+)?(?:visa\s+)?sponsorship',
        r'cannot\s+sponsor',
        r'must\s+be\s+authorized\s+to\s+work\s+in\s+(?:the\s+)?(?:us|u\.s\.|united\s+states)',
        r'without\s+(?:requiring\s+)?(?:visa\s+)?sponsorship',
    ]
    
    US_INDICATORS = [
        'california', 'new york', 'texas', 'washington', 'massachusetts',
        'colorado', 'illinois', 'florida', 'georgia', 'virginia',
        'san francisco', 'san jose', 'los angeles', 'san diego', 'seattle',
        'new york', 'nyc', 'boston', 'austin', 'denver', 'chicago',
        'atlanta', 'miami', 'dallas', 'houston', 'phoenix', 'portland',
        'bay area', 'silicon valley', 'palo alto', 'mountain view',
        'remote', 'united states', 'usa',
    ]
    
    def __init__(self, max_yoe: int = 5):
        self.max_yoe = max_yoe
        self.yoe_patterns = [re.compile(p, re.IGNORECASE) for p in self.YOE_PATTERNS]
        self.citizenship_patterns = [re.compile(p, re.IGNORECASE) for p in self.CITIZENSHIP_PATTERNS]
    
    def _extract_yoe(self, text: str) -> Optional[int]:
        """Extract minimum YOE from text."""
        yoe_values = []
        for pattern in self.yoe_patterns:
            matches = pattern.findall(text)
            for match in matches:
                try:
                    yoe = int(match)
                    if 0 < yoe < 50:
                        yoe_values.append(yoe)
                except (ValueError, TypeError):
                    continue
        return min(yoe_values) if yoe_values else None
    
    def _check_yoe(self, text: str) -> PreFilterResult:
        yoe = self._extract_yoe(text)
        if yoe and yoe > self.max_yoe:
            return PreFilterResult(False, "yoe_exceeded", f"Requires {yoe}+ years (max: {self.max_yoe})")
        return PreFilterResult(True)
    
    def _check_location(self, text: str) -> PreFilterResult:
        text_lower = text.lower()
        for location in self.NON_US_LOCATIONS:
            if location in text_lower:
                # Check context to avoid false positives
                patterns = [
                    rf'(?:location|based|office|located|position).*?{re.escape(location)}',
                    rf'{re.escape(location)}.*?(?:office|location|based)',
                    rf'in\s+{re.escape(location)}',
                ]
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        return PreFilterResult(False, "non_us_location", f"Location: {location}")
        return PreFilterResult(True)
    
    def _check_citizenship(self, text: str) -> PreFilterResult:
        for pattern in self.citizenship_patterns:
            match = pattern.search(text.lower())
            if match:
                return PreFilterResult(False, "citizenship_required", f"Matched: '{match.group()}'")
        return PreFilterResult(True)
    
    def filter(self, content: str, url: str = "") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Apply all pre-parse filters.
        Returns: (passed, reason, details)
        """
        if not content:
            return True, None, None
        
        # Check 1: YOE
        result = self._check_yoe(content)
        if not result.passed:
            return False, result.reason, result.details
        
        # Check 2: Location
        result = self._check_location(content)
        if not result.passed:
            return False, result.reason, result.details
        
        # Check 3: Citizenship
        result = self._check_citizenship(content)
        if not result.passed:
            return False, result.reason, result.details
        
        return True, None, None
    
    def filter_batch(self, extracted_contents: List[dict]) -> Tuple[List[dict], List[dict]]:
        """Filter batch of extracted contents. Returns (passed, filtered)."""
        passed, filtered = [], []
        
        for item in extracted_contents:
            if not item.get("success") or not item.get("content"):
                continue
            
            is_passed, reason, details = self.filter(item["content"], item["url"])
            
            if is_passed:
                passed.append(item)
            else:
                filtered.append({**item, "filter_reason": reason, "filter_details": details})
        
        logger.info(f"Pre-filter: {len(passed)} passed, {len(filtered)} filtered")
        return passed, filtered
