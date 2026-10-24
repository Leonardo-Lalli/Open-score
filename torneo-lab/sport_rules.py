"""Sport-specific rules and configurations for Open Score."""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SportConfig:
    """Configuration for a specific sport"""
    id: int
    name: str
    description: str
    points_system: str
    rules: Dict[str, Any]
    
    def get_team_size_range(self) -> tuple[int, int]:
        """Get minimum and maximum team sizes for this sport"""
        min_size = self.rules.get('min_team_size', 1)
        max_size = self.rules.get('max_team_size', 11)
        return (min_size, max_size)
    
    def get_field_type(self) -> str:
        """Get field/court type for this sport"""
        return self.rules.get('field_type', 'grass')
    
    def supports_sets(self) -> bool:
        """Check if this sport supports set-based scoring"""
        return self.rules.get('set_based_scoring', False)
    
    def supports_time_based(self) -> bool:
        """Check if this sport uses time-based scoring"""
        return self.rules.get('time_based_scoring', False)


# Predefined sport configurations
SPORT_CONFIGS = {
    'Calcio': SportConfig(
        id=1, 
        name='Calcio',
        description='Sport di squadra con regole classiche di calcio',
        points_system='standard',
        rules={
            'max_team_size': 11,
            'min_team_size': 7,
            'field_type': 'grass',
            'ball_type': 'standard',
            'set_based_scoring': False,
            'time_based_scoring': False
        }
    ),
    'Calcio a 5': SportConfig(
        id=2,
        name='Calcio a 5',
        description='Calcio su campo ridotto con 5 giocatori per squadra',
        points_system='standard',
        rules={
            'max_team_size': 5,
            'min_team_size': 5,
            'field_type': 'grass',
            'ball_type': 'small',
            'set_based_scoring': False,
            'time_based_scoring': False
        }
    ),
    'Basket': SportConfig(
        id=3,
        name='Basket',
        description='Sport di squadra con palla e canestro',
        points_system='standard',
        rules={
            'max_team_size': 5,
            'min_team_size': 5,
            'court_type': 'indoor',
            'ball_type': 'basket',
            'set_based_scoring': False,
            'time_based_scoring': False
        }
    ),
    'Pallamano': SportConfig(
        id=4,
        name='Pallamano',
        description='Sport con palla e rete',
        points_system='standard',
        rules={
            'max_team_size': 7,
            'min_team_size': 7,
            'court_type': 'indoor',
            'ball_type': 'handball',
            'set_based_scoring': False,
            'time_based_scoring': False
        }
    ),
    'Badminton': SportConfig(
        id=5,
        name='Badminton',
        description='Sport con racchetta e volano',
        points_system='standard',
        rules={
            'max_team_size': 2,
            'min_team_size': 1,
            'court_type': 'indoor',
            'net_type': 'standard',
            'set_based_scoring': True,
            'time_based_scoring': False
        }
    ),
    'Tennis': SportConfig(
        id=6,
        name='Tennis',
        description='Sport con racchetta e palla',
        points_system='standard',
        rules={
            'max_team_size': 2,
            'min_team_size': 1,
            'court_type': 'outdoor',
            'surface': 'clay',
            'set_based_scoring': True,
            'time_based_scoring': False
        }
    ),
    'Volley': SportConfig(
        id=7,
        name='Volley',
        description='Sport di squadra con rete',
        points_system='standard',
        rules={
            'max_team_size': 6,
            'min_team_size': 6,
            'court_type': 'indoor',
            'net_type': 'standard',
            'set_based_scoring': True,
            'time_based_scoring': False
        }
    ),
    'Pallavolo': SportConfig(
        id=8,
        name='Pallavolo',
        description='Sport con palla e rete',
        points_system='standard',
        rules={
            'max_team_size': 6,
            'min_team_size': 6,
            'court_type': 'indoor',
            'net_type': 'standard',
            'set_based_scoring': True,
            'time_based_scoring': False
        }
    ),
    'Pallacanestro': SportConfig(
        id=9,
        name='Pallacanestro',
        description='Basket specifico (pallacanestro)',
        points_system='standard',
        rules={
            'max_team_size': 5,
            'min_team_size': 5,
            'court_type': 'indoor',
            'ball_type': 'basket',
            'set_based_scoring': False,
            'time_based_scoring': False
        }
    )
}


def get_sport_config_by_name(sport_name: str) -> Optional[SportConfig]:
    """Get sport configuration by name"""
    return SPORT_CONFIGS.get(sport_name)


def get_sport_config_by_id(sport_id: int) -> Optional[SportConfig]:
    """Get sport configuration by ID"""
    for config in SPORT_CONFIGS.values():
        if config.id == sport_id:
            return config
    return None


def validate_team_size_for_sport(sport_name: str, team_size: int) -> bool:
    """Validate if a team size is appropriate for the given sport"""
    config = get_sport_config_by_name(sport_name)
    if not config:
        return True  # Unknown sport, accept anything
    
    min_size, max_size = config.get_team_size_range()
    return min_size <= team_size <= max_size


def get_supported_sports() -> list[str]:
    """Get list of all supported sports"""
    return list(SPORT_CONFIGS.keys())


def get_sport_rules_summary(sport_name: str) -> dict:
    """Get a summary of sport rules for display"""
    config = get_sport_config_by_name(sport_name)
    if not config:
        return {}
    
    return {
        'name': config.name,
        'description': config.description,
        'max_team_size': config.rules.get('max_team_size', 11),
        'min_team_size': config.rules.get('min_team_size', 1),
        'field_type': config.rules.get('field_type', 'grass'),
        'court_type': config.rules.get('court_type', 'indoor'),
        'ball_type': config.rules.get('ball_type', 'standard')
    }