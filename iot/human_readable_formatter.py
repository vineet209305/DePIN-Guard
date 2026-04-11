#!/usr/bin/env python3
"""
IoT Data Formatter for Non-Technical Users

Converts raw sensor data into human-readable explanations
that anyone can understand without technical background.

Examples:
  Raw: device_id=Device-001, temperature=95.5, vibration=8.2, power_usage=125.3
  Formatted: "Mixer is RUNNING NORMALLY - Temp 95°C (hot), Vibration 8.2 (elevated)"
  
  Raw: temperature=115.0, vibration=12.5, power_usage=180.0
  Formatted: "⚠️  ALERT: Mixer shows SIGNS OF FAILURE - Extremely hot (115°C), 
             Vibration critical (12.5), Power usage high (180)"
"""

import pandas as pd
from datetime import datetime
import re


class HumanReadableDataFormatter:
    """Convert sensor data to non-technical language"""
    
    def __init__(self):
        # Temperature ranges (Celsius)
        self.temp_ranges = {
            'cold': (0, 20),
            'normal': (20, 70),
            'warm': (70, 85),
            'hot': (85, 100),
            'critical': (100, 150)
        }
        
        # Vibration ranges (mm/s)
        self.vibration_ranges = {
            'stable': (0, 2),
            'normal': (2, 5),
            'elevated': (5, 8),
            'concerning': (8, 12),
            'severe': (12, 50)
        }
        
        # Power consumption ranges (kW) - relative to machine type
        self.power_ranges = {
            'idle': (0, 10),
            'normal': (10, 100),
            'high': (100, 150),
            'critical': (150, 300)
        }
        
        # Machine type descriptions
        self.machine_descriptions = {
            'Device-000': 'Injection Molder',
            'Device-001': 'Mixer',
            'Device-002': 'Pick & Place',
            'Device-003': 'Vision System',
            'Device-004': 'Shuttle System',
            'Device-005': 'Labeler',
            'Device-006': 'Automated Screwdriver',
            'Device-007': 'Shrink Wrapper',
            'Device-008': 'Laser Cutter',
            'Device-009': 'CMM',
            'Device-010': 'CNC Lathe',
            'Device-011': 'Dryer',
            'Device-012': 'Valve Controller',
            'Device-013': 'Furnace',
            'Device-014': 'Carton Former',
            'Device-015': 'Hydraulic Press',
            'Device-016': 'Compressor',
            'Device-017': 'AGV',
            'Device-018': 'Robot Arm',
            'Device-019': 'Conveyor Belt',
            'Device-020': 'Forklift',
            'Device-021': 'Press Brake',
            'Device-022': 'Boiler',
            'Device-023': 'Vacuum Packer',
            'Device-024': 'XRay Inspector',
            'Device-025': 'Crane',
            'Device-026': '3D Printer',
            'Device-027': 'Palletizer',
            'Device-028': 'Grinder',
            'Device-029': 'CNC Mill',
            'Device-030': 'Chiller',
            'Device-031': 'Heat Exchanger',
            'Device-032': 'Pump'
        }
    
    def categorize_temperature(self, temp):
        """Classify temperature into human terms"""
        for category, (low, high) in self.temp_ranges.items():
            if low <= temp < high:
                return category
        return 'critical'
    
    def categorize_vibration(self, vib):
        """Classify vibration into human terms"""
        for category, (low, high) in self.vibration_ranges.items():
            if low <= vib < high:
                return category
        return 'severe'
    
    def categorize_power(self, power):
        """Classify power consumption into human terms"""
        for category, (low, high) in self.power_ranges.items():
            if low <= power < high:
                return category
        return 'critical'
    
    def get_machine_name(self, device_id):
        """Get human-friendly machine name"""
        return self.machine_descriptions.get(device_id, device_id)
    
    def generate_status_emoji(self, temp_level, vib_level, power_level):
        """Generate emoji based on machine status"""
        # Check for anomalies
        critical_levels = ['critical', 'severe']
        concerning_levels = ['concerning', 'hot', 'high']
        
        if temp_level in critical_levels or vib_level in critical_levels or power_level in critical_levels:
            return "🔴"  # Critical
        elif temp_level in concerning_levels or vib_level in concerning_levels or power_level in concerning_levels:
            return "🟡"  # Warning
        else:
            return "🟢"  # Normal
    
    def format_for_nontechnical_users(self, device_id, temperature, vibration, power_usage, 
                                     anomaly_flag=None, timestamp=None):
        """
        Format sensor reading in plain English for non-technical users
        
        Returns dict with multiple formats:
        - short: One sentence summary
        - details: Full explanation
        - alert_level: 🟢 Normal / 🟡 Warning / 🔴 Critical
        - recommendations: Actions to take
        """
        
        machine_name = self.get_machine_name(device_id)
        
        temp_level = self.categorize_temperature(temperature)
        vib_level = self.categorize_vibration(vibration)
        power_level = self.categorize_power(power_usage)
        status_emoji = self.generate_status_emoji(temp_level, vib_level, power_level)
        
        # Temperature description
        if temp_level == 'cold':
            temp_desc = f"very cold ({temperature}°C)"
            temp_concern = False
        elif temp_level == 'normal':
            temp_desc = f"normal temperature ({temperature}°C)"
            temp_concern = False
        elif temp_level == 'warm':
            temp_desc = f"running warm ({temperature}°C)"
            temp_concern = False
        elif temp_level == 'hot':
            temp_desc = f"running HOT ({temperature}°C) ⚠️ "
            temp_concern = True
        else:  # critical
            temp_desc = f"EXTREMELY HOT ({temperature}°C) 🔴 DANGER!"
            temp_concern = True
        
        # Vibration description
        if vib_level == 'stable':
            vib_desc = f"vibration almost none ({vibration} mm/s)"
            vib_concern = False
        elif vib_level == 'normal':
            vib_desc = f"normal vibration ({vibration} mm/s)"
            vib_concern = False
        elif vib_level == 'elevated':
            vib_desc = f"vibration elevated ({vibration} mm/s)"
            vib_concern = False
        elif vib_level == 'concerning':
            vib_desc = f"vibration concerning ({vibration} mm/s) ⚠️ "
            vib_concern = True
        else:  # severe
            vib_desc = f"vibration SEVERE ({vibration} mm/s) 🔴 INVESTIGATE!"
            vib_concern = True
        
        # Power description
        if power_level == 'idle':
            power_desc = f"idle ({power_usage} kW)"
            power_concern = False
        elif power_level == 'normal':
            power_desc = f"normal power usage ({power_usage} kW)"
            power_concern = False
        elif power_level == 'high':
            power_desc = f"high power usage ({power_usage} kW) ⚠️ "
            power_concern = True
        else:  # critical
            power_desc = f"CRITICAL power usage ({power_usage} kW) 🔴"
            power_concern = True
        
        # Overall assessment
        num_concerns = sum([temp_concern, vib_concern, power_concern])
        
        if num_concerns >= 2:
            overall_status = "LIKELY FAILURE - IMMEDIATE ACTION REQUIRED"
            alert_level = "🔴 CRITICAL"
            short_status = "Machine in trouble"
            recommendations = [
                "Stop machine immediately",
                "Check for burning smells/smoke",
                "Check cooling system",
                "Call maintenance team",
                "Do NOT restart until checked by technician"
            ]
        elif num_concerns == 1:
            overall_status = "WARNING - INCREASED MONITORING REQUIRED"
            alert_level = "🟡 WARNING"
            short_status = "Machine showing warning signs"
            recommendations = [
                "Monitor closely in next hour",
                "Check the specific warning above",
                "Prepare to stop machine if it gets worse",
                "Contact maintenance if issue persists"
            ]
        else:
            overall_status = "NORMAL OPERATION"
            alert_level = "🟢 NORMAL"
            short_status = "Machine running well"
            recommendations = [
                "Continue normal operation",
                "Check status again in 1 hour",
                "No action needed"
            ]
        
        # Format output
        timestamp_str = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        short_format = f"{status_emoji} {machine_name}: {short_status}"
        
        recommendations_text = '\n'.join([f'  {i+1}. {rec}' for i, rec in enumerate(recommendations)])
        
        detailed_format = f"""
{status_emoji} {machine_name} Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Time: {timestamp_str}
Overall Status: {overall_status}

📊 READINGS:
├─ Temperature: {temp_desc}
├─ Vibration: {vib_desc}
└─ Power Usage: {power_desc}

⚠️  ASSESSMENT:
{overall_status}

✅ RECOMMENDED ACTIONS:
{recommendations_text}
        """.strip()
        
        return {
            'device_id': device_id,
            'machine_name': machine_name,
            'short': short_format,
            'details': detailed_format,
            'alert_level': alert_level,
            'status': 'anomaly' if anomaly_flag and anomaly_flag >= 0.5 else 'normal',
            'temperature': {
                'value': temperature,
                'level': temp_level,
                'concern': temp_concern,
                'description': temp_desc
            },
            'vibration': {
                'value': vibration,
                'level': vib_level,
                'concern': vib_concern,
                'description': vib_desc
            },
            'power': {
                'value': power_usage,
                'level': power_level,
                'concern': power_concern,
                'description': power_desc
            },
            'recommendations': recommendations,
            'timestamp': timestamp_str
        }


def demo():
    """Show examples of human-readable formatting"""
    formatter = HumanReadableDataFormatter()
    
    print("="*70)
    print("IoT DATA FORMATTING FOR NON-TECHNICAL USERS - EXAMPLES")
    print("="*70)
    
    # Example 1: Normal operation
    print("\n🟢 EXAMPLE 1: Normal Machine Operation")
    print("-" * 70)
    result1 = formatter.format_for_nontechnical_users(
        device_id='Device-001',
        temperature=65.0,
        vibration=3.5,
        power_usage=50.0,
        anomaly_flag=0
    )
    print(result1['details'])
    
    # Example 2: Warning
    print("\n🟡 EXAMPLE 2: Warning - Monitor Closely")
    print("-" * 70)
    result2 = formatter.format_for_nontechnical_users(
        device_id='Device-016',
        temperature=92.0,
        vibration=9.5,
        power_usage=80.0,
        anomaly_flag=0.3
    )
    print(result2['details'])
    
    # Example 3: Critical
    print("\n🔴 EXAMPLE 3: Critical - Immediate Action Required")
    print("-" * 70)
    result3 = formatter.format_for_nontechnical_users(
        device_id='Device-030',
        temperature=118.0,
        vibration=14.2,
        power_usage=175.0,
        anomaly_flag=1
    )
    print(result3['details'])
    
    print("\n" + "="*70)
    print("✅ Format ready for non-technical user display!")
    print("="*70)


if __name__ == '__main__':
    demo()
