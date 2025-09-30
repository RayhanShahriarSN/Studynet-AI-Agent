# Entity extraction from natural language queries
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class EntityMatch:
    """Matched entity with metadata"""
    raw: str
    normalized: Any
    confidence: float

class EntityExtractor:
    """Extract structured entities from natural language queries"""

    def __init__(self):
        self.field_mapper = FieldOfStudyMapper()
        self.location_mapper = LocationMapper()
        self.provider_mapper = ProviderNameMapper()
        self.price_extractor = PriceExtractor()
        self.study_level_extractor = StudyLevelExtractor()

    def extract(self, query: str) -> List:
        """Extract all entities from query"""
        from .classifier import Entity

        entities = []

        # Extract field of study
        field = self.field_mapper.extract(query)
        if field:
            entities.append(Entity(
                type="field_of_study",
                value=field.raw,
                normalized_value=field.normalized,
                confidence=field.confidence
            ))

        # Extract location
        location = self.location_mapper.extract(query)
        if location:
            entities.append(Entity(
                type="location",
                value=location.raw,
                normalized_value=location.normalized,
                confidence=location.confidence
            ))

        # Extract price range
        price = self.price_extractor.extract(query)
        if price:
            entities.append(Entity(
                type="price_range",
                value=price.raw,
                normalized_value=price.normalized,
                confidence=price.confidence
            ))

        # Extract provider name
        provider = self.provider_mapper.extract(query)
        if provider:
            entities.append(Entity(
                type="provider_name",
                value=provider.raw,
                normalized_value=provider.normalized,
                confidence=provider.confidence
            ))

        # Extract study level
        level = self.study_level_extractor.extract(query)
        if level:
            entities.append(Entity(
                type="study_level",
                value=level.raw,
                normalized_value=level.normalized,
                confidence=level.confidence
            ))

        # Extract boolean flags
        if re.search(r'\b(with|has|have|offer|offers)\s+scholarship', query, re.IGNORECASE):
            entities.append(Entity(
                type="has_scholarship",
                value="with scholarship",
                normalized_value=True,
                confidence=0.95
            ))

        if re.search(r'\b(with|has|have|offer|offers)\s+internship', query, re.IGNORECASE):
            entities.append(Entity(
                type="has_internship",
                value="with internship",
                normalized_value=True,
                confidence=0.95
            ))

        # Extract ranking criteria
        ranking_match = re.search(r'top\s+(\d+)|rank(?:ed|ing)\s+(?:under|below|top)\s+(\d+)', query, re.IGNORECASE)
        if ranking_match:
            ranking = int(ranking_match.group(1) or ranking_match.group(2))
            entities.append(Entity(
                type="ranking",
                value=ranking_match.group(0),
                normalized_value=ranking,
                confidence=0.9
            ))

        logger.info(f"Extracted {len(entities)} entities from query")
        return entities


class FieldOfStudyMapper:
    """Map student terms to database field values"""

    # Comprehensive field mappings
    FIELD_MAPPINGS = {
        # IT & Computing
        'it': ['Information Technology', 'Information technologies', 'Computing'],
        'information technology': ['Information Technology', 'Information technologies'],
        'computer science': ['Computer Science', 'Information Technology', 'Computing'],
        'computing': ['Computing', 'Information Technology'],
        'software engineering': ['Information Technology', 'Engineering'],
        'software': ['Information Technology'],
        'ai': ['Artificial Intelligence', 'Information Technology', 'Computer Science'],
        'artificial intelligence': ['Artificial Intelligence', 'Information Technology'],
        'data science': ['Information Technology', 'Computer Science'],
        'cybersecurity': ['Information Technology', 'Computer Science'],
        'cyber security': ['Information Technology', 'Computer Science'],

        # Business
        'business': ['Business', 'Business Studies', 'Commerce'],
        'commerce': ['Commerce', 'Business'],
        'accounting': ['Accounting', 'Accounting Practice', 'Business'],
        'finance': ['Applied Finance', 'Business', 'Commerce'],
        'management': ['Business', 'Business Studies'],
        'mba': ['Business', 'Business Studies'],
        'marketing': ['Business', 'Commerce'],

        # Engineering
        'engineering': ['Engineering', 'Architecture And Building'],
        'civil engineering': ['Engineering', 'Architecture And Building'],
        'mechanical engineering': ['Engineering'],
        'electrical engineering': ['Engineering'],

        # Medicine & Health
        'medicine': ['Medicine', 'Health Sciences', 'Medical'],
        'medical': ['Medicine', 'Medical Science', 'Health'],
        'health': ['Health', 'Health Sciences', 'Medicine'],
        'nursing': ['Nursing', 'Health'],
        'pharmacy': ['Pharmacy', 'Health Sciences'],

        # Science
        'science': ['Science', 'Sciences'],
        'biology': ['Science', 'Biological Sciences'],
        'chemistry': ['Science', 'Chemical Sciences'],
        'physics': ['Science', 'Physical Sciences'],
        'mathematics': ['Science', 'Mathematics'],
        'math': ['Science', 'Mathematics'],

        # Arts & Humanities
        'arts': ['Arts', 'Arts and Social Sciences', 'Humanities'],
        'humanities': ['Arts', 'Arts, Humanities And Social Science'],
        'social science': ['Arts', 'Arts and Social Sciences', 'Social Sciences'],
        'psychology': ['Psychology', 'Arts and Social Sciences'],

        # Law
        'law': ['Law', 'Legal Studies', 'Laws'],
        'legal': ['Law', 'Legal Studies'],

        # Education
        'education': ['Education', 'Teaching'],
        'teaching': ['Education', 'Teaching'],
    }

    def extract(self, query: str) -> Optional[EntityMatch]:
        """Extract field of study from query"""
        query_lower = query.lower()

        # Try exact match first
        for student_term, db_values in self.FIELD_MAPPINGS.items():
            # Use word boundaries to avoid false matches
            pattern = r'\b' + re.escape(student_term) + r'\b'
            if re.search(pattern, query_lower):
                logger.info(f"Matched field: '{student_term}' -> {db_values}")
                return EntityMatch(
                    raw=student_term,
                    normalized=db_values,
                    confidence=0.9
                )

        return None


class LocationMapper:
    """Map location names to city/state"""

    # Australian cities and states
    CITY_STATE_MAP = {
        # Major cities
        'sydney': {'city': 'Sydney', 'state': 'New South Wales'},
        'melbourne': {'city': 'Melbourne', 'state': 'Victoria'},
        'brisbane': {'city': 'Brisbane', 'state': 'Queensland'},
        'perth': {'city': 'Perth', 'state': 'Western Australia'},
        'adelaide': {'city': 'Adelaide', 'state': 'South Australia'},
        'canberra': {'city': 'Canberra', 'state': 'Australian Capital Territory'},
        'hobart': {'city': 'Hobart', 'state': 'Tasmania'},
        'darwin': {'city': 'Darwin', 'state': 'Northern Territory'},

        # Other cities
        'gold coast': {'city': 'Gold Coast', 'state': 'Queensland'},
        'newcastle': {'city': 'Newcastle', 'state': 'New South Wales'},
        'wollongong': {'city': 'Wollongong', 'state': 'New South Wales'},
        'geelong': {'city': 'Geelong', 'state': 'Victoria'},
        'townsville': {'city': 'Townsville', 'state': 'Queensland'},
        'cairns': {'city': 'Cairns', 'state': 'Queensland'},

        # State names
        'new south wales': {'state': 'New South Wales'},
        'nsw': {'state': 'New South Wales'},
        'victoria': {'state': 'Victoria'},
        'vic': {'state': 'Victoria'},
        'queensland': {'state': 'Queensland'},
        'qld': {'state': 'Queensland'},
        'western australia': {'state': 'Western Australia'},
        'wa': {'state': 'Western Australia'},
        'south australia': {'state': 'South Australia'},
        'sa': {'state': 'South Australia'},
        'tasmania': {'state': 'Tasmania'},
        'tas': {'state': 'Tasmania'},
        'northern territory': {'state': 'Northern Territory'},
        'nt': {'state': 'Northern Territory'},
        'act': {'state': 'Australian Capital Territory'},
    }

    def extract(self, query: str) -> Optional[EntityMatch]:
        """Extract location from query"""
        query_lower = query.lower()

        # Try to match cities/states (longer names first)
        sorted_locations = sorted(self.CITY_STATE_MAP.keys(), key=len, reverse=True)

        for location in sorted_locations:
            pattern = r'\b' + re.escape(location) + r'\b'
            if re.search(pattern, query_lower):
                logger.info(f"Matched location: '{location}' -> {self.CITY_STATE_MAP[location]}")
                return EntityMatch(
                    raw=location,
                    normalized=self.CITY_STATE_MAP[location],
                    confidence=0.95
                )

        return None


class ProviderNameMapper:
    """Map university names and aliases"""

    # Common university aliases
    PROVIDER_ALIASES = {
        'unsw': 'University of New South Wales',
        'usyd': 'University of Sydney',
        'sydney uni': 'University of Sydney',
        'uts': 'University of Technology Sydney',
        'macquarie': 'Macquarie University',
        'uq': 'University of Queensland',
        'queensland uni': 'University of Queensland',
        'monash': 'Monash University',
        'unimelb': 'University of Melbourne',
        'melbourne uni': 'University of Melbourne',
        'rmit': 'RMIT University',
        'deakin': 'Deakin University',
        'griffith': 'Griffith University',
        'qut': 'Queensland University of Technology',
        'anu': 'Australian National University',
        'uwa': 'University of Western Australia',
        'western australia uni': 'University of Western Australia',
        'adelaide uni': 'University of Adelaide',
        'utas': 'University of Tasmania',
        'cdu': 'Charles Darwin University',
        'csu': 'Charles Sturt University',
        'victoria uni': 'Victoria University',
    }

    def extract(self, query: str) -> Optional[EntityMatch]:
        """Extract provider name from query"""
        query_lower = query.lower()

        # Try aliases first
        for alias, full_name in self.PROVIDER_ALIASES.items():
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, query_lower):
                logger.info(f"Matched provider: '{alias}' -> {full_name}")
                return EntityMatch(
                    raw=alias,
                    normalized=full_name,
                    confidence=0.95
                )

        # Try to find "university" keyword and extract name
        uni_pattern = r'(\w+(?:\s+\w+)?)\s+university'
        match = re.search(uni_pattern, query_lower)
        if match:
            name = match.group(0).title()
            logger.info(f"Found university name: {name}")
            return EntityMatch(
                raw=name,
                normalized=name,
                confidence=0.8
            )

        return None


class PriceExtractor:
    """Extract price ranges from queries"""

    PATTERNS = [
        (r'under\s+\$?(\d+k?)\b', 'under'),
        (r'less\s+than\s+\$?(\d+k?)\b', 'under'),
        (r'below\s+\$?(\d+k?)\b', 'under'),
        (r'cheaper\s+than\s+\$?(\d+k?)\b', 'under'),
        (r'maximum\s+\$?(\d+k?)\b', 'under'),
        (r'up\s+to\s+\$?(\d+k?)\b', 'under'),
        (r'between\s+\$?(\d+k?)\s+and\s+\$?(\d+k?)\b', 'range'),
        (r'\$?(\d+k?)\s+to\s+\$?(\d+k?)\b', 'range'),
        (r'from\s+\$?(\d+k?)\s+to\s+\$?(\d+k?)\b', 'range'),
        (r'over\s+\$?(\d+k?)\b', 'over'),
        (r'more\s+than\s+\$?(\d+k?)\b', 'over'),
        (r'above\s+\$?(\d+k?)\b', 'over'),
    ]

    def extract(self, query: str) -> Optional[EntityMatch]:
        """Extract price constraints"""

        for pattern, price_type in self.PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                raw_text = match.group(0)

                if price_type == 'under':
                    max_val = self._parse_value(match.group(1))
                    normalized = {'min': 0, 'max': max_val}
                    logger.info(f"Extracted price: under ${max_val}")

                elif price_type == 'over':
                    min_val = self._parse_value(match.group(1))
                    normalized = {'min': min_val, 'max': 999999}
                    logger.info(f"Extracted price: over ${min_val}")

                elif price_type == 'range':
                    min_val = self._parse_value(match.group(1))
                    max_val = self._parse_value(match.group(2))
                    normalized = {'min': min_val, 'max': max_val}
                    logger.info(f"Extracted price range: ${min_val} - ${max_val}")

                return EntityMatch(
                    raw=raw_text,
                    normalized=normalized,
                    confidence=0.95
                )

        return None

    def _parse_value(self, value: str) -> float:
        """Parse '20k' → 20000.0"""
        value = value.strip().replace('$', '').replace(',', '')
        if value.endswith('k') or value.endswith('K'):
            return float(value[:-1]) * 1000
        return float(value)


class StudyLevelExtractor:
    """Extract study level from query"""

    LEVEL_MAPPINGS = {
        'bachelor': 'Bachelor Degree',
        "bachelor's": 'Bachelor Degree',
        'undergraduate': 'Undergraduate',
        'undergrad': 'Undergraduate',
        'bachelor degree': 'Bachelor Degree',
        'master': 'Master Degree',
        "master's": 'Master Degree',
        'masters': 'Master Degree',
        'postgraduate': 'Postgraduate',
        'postgrad': 'Postgraduate',
        'master degree': 'Master Degree',
        'phd': 'Doctorate Degree',
        'doctorate': 'Doctorate Degree',
        'doctoral': 'Doctorate Degree',
        'diploma': 'Diploma',
        'certificate': 'Certificate',
        'grad cert': 'Graduate Certificate',
        'graduate certificate': 'Graduate Certificate',
        'grad dip': 'Graduate Diploma',
        'graduate diploma': 'Graduate Diploma',
    }

    def extract(self, query: str) -> Optional[EntityMatch]:
        """Extract study level"""
        query_lower = query.lower()

        for term, level in self.LEVEL_MAPPINGS.items():
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, query_lower):
                logger.info(f"Matched study level: '{term}' -> {level}")
                return EntityMatch(
                    raw=term,
                    normalized=level,
                    confidence=0.9
                )

        return None
