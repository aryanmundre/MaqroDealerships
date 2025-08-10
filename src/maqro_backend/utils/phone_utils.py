"""
Centralized phone number utilities for consistent handling throughout the application.

This module provides a single standard for phone number normalization:
- Format: +1xxxxxxxxxx for US numbers (e.g., +15551234567)  
- Format: +xxxxxxxxxxxx for international numbers
- Storage: Always stored with country code prefix
- Lookup: Exact match on normalized format
"""
import re
from typing import Optional


def normalize_phone_number(phone: str) -> Optional[str]:
    """
    Normalize phone number to a consistent format for storage and comparison.
    
    Standard format:
    - US numbers: +1xxxxxxxxxx (e.g., +15551234567)
    - International: +xxxxxxxxxxxx
    
    Args:
        phone: Raw phone number in any format
        
    Returns:
        Normalized phone number with country code prefix, or None if invalid
    """
    if not phone or not isinstance(phone, str):
        return None
    
    # Remove all non-digit characters
    digits_only = re.sub(r'[^\d]', '', phone)
    
    if not digits_only:
        return None
    
    # Handle US numbers
    if len(digits_only) == 10:
        # Assume US number, add country code
        return f"+1{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        # US number with country code
        return f"+{digits_only}"
    elif len(digits_only) > 11:
        # International number, keep as is
        return f"+{digits_only}"
    elif len(digits_only) < 10:
        # Too short to be valid
        return None
    else:
        # 10+ digit international number without country code
        return f"+{digits_only}"


def are_phones_equivalent(phone1: str, phone2: str) -> bool:
    """
    Compare two phone numbers for equivalence after normalization.
    
    Args:
        phone1: First phone number
        phone2: Second phone number
        
    Returns:
        True if phones are equivalent, False otherwise
    """
    norm1 = normalize_phone_number(phone1)
    norm2 = normalize_phone_number(phone2)
    
    if not norm1 or not norm2:
        return False
        
    return norm1 == norm2


def format_phone_display(phone: str) -> str:
    """
    Format phone number for display purposes.
    
    Args:
        phone: Normalized phone number
        
    Returns:
        Formatted phone number for display (e.g., +1 (555) 123-4567)
    """
    normalized = normalize_phone_number(phone)
    if not normalized:
        return phone  # Return original if can't normalize
        
    if normalized.startswith('+1') and len(normalized) == 12:
        # US number: +1 (555) 123-4567
        digits = normalized[2:]  # Remove +1
        return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    else:
        # International number: keep as +xxxxxxxxxxxx
        return normalized


def extract_digits_only(phone: str) -> str:
    """
    Extract only digits from phone number (for legacy compatibility).
    
    Args:
        phone: Phone number in any format
        
    Returns:
        Digits only (no country code prefix)
    """
    normalized = normalize_phone_number(phone)
    if not normalized:
        return ""
        
    if normalized.startswith('+1'):
        return normalized[2:]  # Remove +1
    elif normalized.startswith('+'):
        return normalized[1:]  # Remove +
    else:
        return normalized