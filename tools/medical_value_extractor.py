"""
Rule-Based Medical Value Extractor
Extracts medical values from OCR text and applies simple rules.
NO DIAGNOSIS - Only risk indication.
"""
import logging
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Medical value patterns
MEDICAL_PATTERNS = {
    "cholesterol": [
        r"cholesterol[:\s]+(\d+(?:\.\d+)?)",
        r"total\s+cholesterol[:\s]+(\d+(?:\.\d+)?)",
        r"chol[:\s]+(\d+(?:\.\d+)?)",
    ],
    "ldl": [
        r"ldl[:\s]+(\d+(?:\.\d+)?)",
        r"ldl\s+cholesterol[:\s]+(\d+(?:\.\d+)?)",
        r"low\s+density\s+lipoprotein[:\s]+(\d+(?:\.\d+)?)",
    ],
    "hdl": [
        r"hdl[:\s]+(\d+(?:\.\d+)?)",
        r"hdl\s+cholesterol[:\s]+(\d+(?:\.\d+)?)",
        r"high\s+density\s+lipoprotein[:\s]+(\d+(?:\.\d+)?)",
    ],
    "triglycerides": [
        r"triglycerides?[:\s]+(\d+(?:\.\d+)?)",
        r"tg[:\s]+(\d+(?:\.\d+)?)",
    ],
    "sugar": [
        r"blood\s+sugar[:\s]+(\d+(?:\.\d+)?)",
        r"glucose[:\s]+(\d+(?:\.\d+)?)",
        r"blood\s+glucose[:\s]+(\d+(?:\.\d+)?)",
        r"fbs[:\s]+(\d+(?:\.\d+)?)",  # Fasting Blood Sugar
        r"rbs[:\s]+(\d+(?:\.\d+)?)",  # Random Blood Sugar
        r"sugar[:\s]+(\d+(?:\.\d+)?)",
    ],
    "bp_systolic": [
        r"bp[:\s]+(\d+)\s*/\s*\d+",
        r"blood\s+pressure[:\s]+(\d+)\s*/\s*\d+",
        r"systolic[:\s]+(\d+)",
        r"(\d+)\s*/\s*\d+\s*mmhg",
    ],
    "bp_diastolic": [
        r"bp[:\s]+\d+\s*/\s*(\d+)",
        r"blood\s+pressure[:\s]+\d+\s*/\s*(\d+)",
        r"diastolic[:\s]+(\d+)",
        r"\d+\s*/\s*(\d+)\s*mmhg",
    ],
    "hemoglobin": [
        r"hemoglobin[:\s]+(\d+(?:\.\d+)?)",
        r"hb[:\s]+(\d+(?:\.\d+)?)",
        r"hgb[:\s]+(\d+(?:\.\d+)?)",
    ],
    "hb1ac": [
        r"hba1c[:\s]+(\d+(?:\.\d+)?)",
        r"hb\s*a1c[:\s]+(\d+(?:\.\d+)?)",
        r"glycated\s+hemoglobin[:\s]+(\d+(?:\.\d+)?)",
    ],
}

# Normal ranges (for adults)
NORMAL_RANGES = {
    "cholesterol": {"min": 0, "max": 200, "high": 240},
    "ldl": {"min": 0, "max": 100, "high": 160},
    "hdl": {"min": 40, "max": 200, "low": 40},
    "triglycerides": {"min": 0, "max": 150, "high": 200},
    "sugar": {"min": 70, "max": 100, "high": 126},  # Fasting
    "bp_systolic": {"min": 90, "max": 120, "high": 140},
    "bp_diastolic": {"min": 60, "max": 80, "high": 90},
    "hemoglobin": {"min": 12.0, "max": 17.5, "low": 12.0},  # Adult male
    "hb1ac": {"min": 4.0, "max": 5.6, "high": 6.5},
}

# Specialty mapping based on findings
FINDING_SPECIALTY_MAP = {
    "high_cholesterol": "Cardiologist",
    "high_ldl": "Cardiologist",
    "low_hdl": "Cardiologist",
    "high_triglycerides": "Cardiologist",
    "high_bp": "Cardiologist",
    "high_sugar": "Endocrinologist",
    "high_hb1ac": "Endocrinologist",
    "low_hemoglobin": "Hematologist",
    "high_hemoglobin": "Hematologist",
}


def extract_medical_values(text: str) -> Dict[str, Any]:
    """
    Extract medical values from text using pattern matching.
    
    Args:
        text: OCR extracted text
        
    Returns:
        Dict with extracted values
    """
    if not text:
        return {}
    
    text_lower = text.lower()
    extracted = {}
    
    for key, patterns in MEDICAL_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    extracted[key] = value
                    logger.info(f"Extracted {key}: {value}")
                    break  # Take first match
                except (ValueError, IndexError):
                    continue
    
    return extracted


def assess_medical_values(values: Dict[str, float]) -> Dict[str, Any]:
    """
    Assess medical values and return findings, severity, and recommended specialty.
    
    NO DIAGNOSIS - Only risk indication.
    
    Args:
        values: Extracted medical values
        
    Returns:
        {
            "findings": ["High Cholesterol", "High LDL"],
            "severity": "medium" | "high" | "low",
            "recommended_specialty": "Cardiologist"
        }
    """
    findings = []
    severity_scores = []
    specialties = []
    
    # Check each value against normal ranges
    for key, value in values.items():
        if key not in NORMAL_RANGES:
            continue
        
        range_info = NORMAL_RANGES[key]
        
        # Check for high values
        if "high" in range_info:
            if value > range_info["high"]:
                finding_name = key.replace("_", " ").title()
                findings.append(f"High {finding_name}")
                severity_scores.append(2)  # High severity
                if key in FINDING_SPECIALTY_MAP:
                    specialties.append(FINDING_SPECIALTY_MAP[key])
        
        # Check for low values
        if "low" in range_info:
            if value < range_info["low"]:
                finding_name = key.replace("_", " ").title()
                findings.append(f"Low {finding_name}")
                severity_scores.append(1)  # Medium severity
                if key in FINDING_SPECIALTY_MAP:
                    specialties.append(FINDING_SPECIALTY_MAP[key])
        
        # Check if above normal but not high
        if value > range_info.get("max", float('inf')):
            if "high" not in range_info or value <= range_info.get("high", float('inf')):
                finding_name = key.replace("_", " ").title()
                findings.append(f"Elevated {finding_name}")
                severity_scores.append(1)  # Medium severity
    
    # Determine overall severity
    if not findings:
        severity = "low"
    elif max(severity_scores) >= 2:
        severity = "high"
    elif max(severity_scores) >= 1:
        severity = "medium"
    else:
        severity = "low"
    
    # Get recommended specialty (most common)
    recommended_specialty = None
    if specialties:
        # Count specialties and get most common
        specialty_counts = {}
        for spec in specialties:
            specialty_counts[spec] = specialty_counts.get(spec, 0) + 1
        recommended_specialty = max(specialty_counts, key=specialty_counts.get)
    
    return {
        "findings": findings,
        "severity": severity,
        "recommended_specialty": recommended_specialty,
        "extracted_values": values
    }


def analyze_medical_report(text: str) -> Dict[str, Any]:
    """
    Complete pipeline: Extract values and assess.
    
    Args:
        text: OCR extracted text
        
    Returns:
        {
            "findings": [...],
            "severity": "low" | "medium" | "high",
            "recommended_specialty": "...",
            "extracted_values": {...}
        }
    """
    if not text:
        return {
            "findings": [],
            "severity": "low",
            "recommended_specialty": None,
            "extracted_values": {}
        }
    
    # Extract values
    values = extract_medical_values(text)
    
    if not values:
        logger.info("No medical values found in text")
        return {
            "findings": [],
            "severity": "low",
            "recommended_specialty": None,
            "extracted_values": {}
        }
    
    # Assess values
    assessment = assess_medical_values(values)
    
    logger.info(f"Medical assessment: {assessment['severity']} severity, {len(assessment['findings'])} findings")
    
    return assessment
