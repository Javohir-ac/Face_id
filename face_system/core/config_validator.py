"""
Configuration Validator - Validate and sanitize system configuration
"""
import json
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from .error_handler import get_error_handler, handle_errors

class ConfigValidator:
    """Professional configuration validation"""
    
    def __init__(self):
        self.error_handler = get_error_handler()
        
        # Define configuration schema
        self.config_schema = {
            'web_port': {'type': int, 'min': 1024, 'max': 65535, 'default': 5000},
            'confidence_threshold': {'type': float, 'min': 0.1, 'max': 1.0, 'default': 0.6},
            'recognition_cooldown': {'type': int, 'min': 10, 'max': 300, 'default': 60},
            'camera_index': {'type': int, 'min': 0, 'max': 10, 'default': 0},
            'zones': {
                'type': dict,
                'required_keys': ['entry_zone', 'neutral_zone', 'exit_zone'],
                'default': {
                    'entry_zone': {'x': 0, 'width': 0.3},
                    'neutral_zone': {'x': 0.3, 'width': 0.4},
                    'exit_zone': {'x': 0.7, 'width': 0.3}
                }
            },
            'auto_backup_hours': {
                'type': list,
                'item_type': int,
                'min_items': 1,
                'max_items': 24,
                'item_min': 0,
                'item_max': 23,
                'default': [9, 13, 17, 21]
            },
            'scheduler': {
                'type': dict,
                'optional': True,
                'default': {
                    'end_of_day_time': '23:59',
                    'weekly_cleanup_day': 'sunday',
                    'weekly_cleanup_time': '02:00',
                    'performance_log_time': '23:58',
                    'enabled': True
                }
            }
        }
        
        print("⚙️  ConfigValidator initialized")
    
    @handle_errors("Configuration Validation")
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize configuration"""
        validated_config = {}
        validation_errors = []
        validation_warnings = []
        
        # Validate each field
        for field_name, field_schema in self.config_schema.items():
            try:
                value = config.get(field_name)
                
                # Check if field is required
                if value is None:
                    if field_schema.get('optional', False):
                        # Use default value for optional fields
                        validated_config[field_name] = field_schema.get('default')
                        continue
                    else:
                        # Use default value and warn
                        validated_config[field_name] = field_schema.get('default')
                        validation_warnings.append(f"Missing field '{field_name}', using default: {field_schema.get('default')}")
                        continue
                
                # Validate field type and constraints
                validated_value, field_errors = self._validate_field(field_name, value, field_schema)
                
                if field_errors:
                    validation_errors.extend(field_errors)
                    # Use default value on error
                    validated_config[field_name] = field_schema.get('default')
                else:
                    validated_config[field_name] = validated_value
                    
            except Exception as e:
                self.error_handler.log_error(e, f"Field validation: {field_name}")
                validation_errors.append(f"Error validating field '{field_name}': {str(e)}")
                validated_config[field_name] = field_schema.get('default')
        
        # Log validation results
        if validation_errors:
            for error in validation_errors:
                self.error_handler.log_warning(error, "Config Validation")
        
        if validation_warnings:
            for warning in validation_warnings:
                self.error_handler.log_warning(warning, "Config Validation")
        
        # Add validation metadata
        validated_config['_validation'] = {
            'timestamp': datetime.now().isoformat(),
            'errors': validation_errors,
            'warnings': validation_warnings,
            'is_valid': len(validation_errors) == 0
        }
        
        return validated_config
    
    def _validate_field(self, field_name: str, value: Any, schema: Dict[str, Any]) -> tuple:
        """Validate individual field"""
        errors = []
        
        try:
            expected_type = schema['type']
            
            # Type validation
            if expected_type == int:
                if not isinstance(value, int):
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        errors.append(f"Field '{field_name}' must be an integer")
                        return None, errors
                
                # Range validation
                if 'min' in schema and value < schema['min']:
                    errors.append(f"Field '{field_name}' must be >= {schema['min']}")
                if 'max' in schema and value > schema['max']:
                    errors.append(f"Field '{field_name}' must be <= {schema['max']}")
            
            elif expected_type == float:
                if not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        errors.append(f"Field '{field_name}' must be a number")
                        return None, errors
                
                # Range validation
                if 'min' in schema and value < schema['min']:
                    errors.append(f"Field '{field_name}' must be >= {schema['min']}")
                if 'max' in schema and value > schema['max']:
                    errors.append(f"Field '{field_name}' must be <= {schema['max']}")
            
            elif expected_type == str:
                if not isinstance(value, str):
                    errors.append(f"Field '{field_name}' must be a string")
                    return None, errors
                
                # Length validation
                if 'min_length' in schema and len(value) < schema['min_length']:
                    errors.append(f"Field '{field_name}' must be at least {schema['min_length']} characters")
                if 'max_length' in schema and len(value) > schema['max_length']:
                    errors.append(f"Field '{field_name}' must be at most {schema['max_length']} characters")
            
            elif expected_type == list:
                if not isinstance(value, list):
                    errors.append(f"Field '{field_name}' must be a list")
                    return None, errors
                
                # List size validation
                if 'min_items' in schema and len(value) < schema['min_items']:
                    errors.append(f"Field '{field_name}' must have at least {schema['min_items']} items")
                if 'max_items' in schema and len(value) > schema['max_items']:
                    errors.append(f"Field '{field_name}' must have at most {schema['max_items']} items")
                
                # Item type validation
                if 'item_type' in schema:
                    item_type = schema['item_type']
                    for i, item in enumerate(value):
                        if not isinstance(item, item_type):
                            errors.append(f"Field '{field_name}[{i}]' must be of type {item_type.__name__}")
                        
                        # Item range validation
                        if item_type in [int, float]:
                            if 'item_min' in schema and item < schema['item_min']:
                                errors.append(f"Field '{field_name}[{i}]' must be >= {schema['item_min']}")
                            if 'item_max' in schema and item > schema['item_max']:
                                errors.append(f"Field '{field_name}[{i}]' must be <= {schema['item_max']}")
            
            elif expected_type == dict:
                if not isinstance(value, dict):
                    errors.append(f"Field '{field_name}' must be a dictionary")
                    return None, errors
                
                # Required keys validation
                if 'required_keys' in schema:
                    for required_key in schema['required_keys']:
                        if required_key not in value:
                            errors.append(f"Field '{field_name}' must contain key '{required_key}'")
            
            return value, errors
            
        except Exception as e:
            self.error_handler.log_error(e, f"Field validation error: {field_name}")
            errors.append(f"Validation error for field '{field_name}': {str(e)}")
            return None, errors
    
    @handle_errors("Config File Validation")
    def validate_config_file(self, config_path: str) -> Optional[Dict[str, Any]]:
        """Validate configuration file"""
        try:
            if not os.path.exists(config_path):
                self.error_handler.log_warning(f"Config file not found: {config_path}", "Config Validation")
                return self._create_default_config()
            
            # Load configuration
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate configuration
            validated_config = self.validate_config(config)
            
            # Save validated configuration back to file
            if not validated_config['_validation']['is_valid']:
                self._backup_config_file(config_path)
                self._save_validated_config(config_path, validated_config)
            
            return validated_config
            
        except json.JSONDecodeError as e:
            self.error_handler.log_error(e, f"Invalid JSON in config file: {config_path}")
            self._backup_config_file(config_path)
            return self._create_default_config()
        
        except Exception as e:
            self.error_handler.log_error(e, f"Config file validation: {config_path}")
            return None
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        default_config = {}
        
        for field_name, field_schema in self.config_schema.items():
            default_config[field_name] = field_schema.get('default')
        
        default_config['_validation'] = {
            'timestamp': datetime.now().isoformat(),
            'errors': [],
            'warnings': ['Using default configuration'],
            'is_valid': True
        }
        
        print("⚙️  Created default configuration")
        return default_config
    
    def _backup_config_file(self, config_path: str):
        """Backup existing config file"""
        try:
            if os.path.exists(config_path):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{config_path}.backup_{timestamp}"
                
                import shutil
                shutil.copy2(config_path, backup_path)
                
                print(f"📋 Config backup created: {backup_path}")
                
        except Exception as e:
            self.error_handler.log_error(e, "Config backup")
    
    def _save_validated_config(self, config_path: str, validated_config: Dict[str, Any]):
        """Save validated configuration"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(validated_config, f, indent=2, ensure_ascii=False)
            
            print(f"⚙️  Validated config saved: {config_path}")
            
        except Exception as e:
            self.error_handler.log_error(e, "Validated config save")
    
    def print_validation_report(self, config: Dict[str, Any]):
        """Print configuration validation report"""
        validation = config.get('_validation', {})
        
        print("\n" + "="*50)
        print("⚙️  CONFIGURATION VALIDATION REPORT")
        print("="*50)
        print(f"Timestamp: {validation.get('timestamp', 'Unknown')}")
        print(f"Valid: {'✅ Yes' if validation.get('is_valid', False) else '❌ No'}")
        
        errors = validation.get('errors', [])
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for error in errors:
                print(f"   • {error}")
        
        warnings = validation.get('warnings', [])
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"   • {warning}")
        
        if not errors and not warnings:
            print("\n✅ No issues found")
        
        print("="*50)

# Global config validator instance
_config_validator = None

def get_config_validator() -> ConfigValidator:
    """Get global config validator instance"""
    global _config_validator
    if _config_validator is None:
        _config_validator = ConfigValidator()
    return _config_validator