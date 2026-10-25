"""Sport catalog read from the single source of truth: `sport_configs`."""

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SportConfig:
    """Configuration for a specific sport, loaded from the database."""

    id: int
    name: str
    description: str
    points_system: str
    rules: dict[str, Any] = field(default_factory=dict)

    def get_team_size_range(self) -> tuple[int, int]:
        return (self.rules.get('min_team_size', 1), self.rules.get('max_team_size', 11))

    def get_field_type(self) -> str:
        return self.rules.get('field_type') or self.rules.get('court_type', 'grass')

    def supports_sets(self) -> bool:
        return bool(self.rules.get('set_based_scoring', False))

    def supports_time_based(self) -> bool:
        return bool(self.rules.get('time_based_scoring', False))


def _from_row(row) -> SportConfig:
    try:
        rules = json.loads(row['rules'] or '{}')
    except (TypeError, ValueError):
        rules = {}
    return SportConfig(
        id=row['id'],
        name=row['name'],
        description=row['description'],
        points_system=row['points_system'],
        rules=rules if isinstance(rules, dict) else {},
    )


def list_configs(db) -> list[SportConfig]:
    """Return every configured sport, ordered by catalog id."""
    return [_from_row(row) for row in db.execute('SELECT * FROM sport_configs ORDER BY id')]


def get_config(db, sport_name: str) -> SportConfig | None:
    row = db.execute('SELECT * FROM sport_configs WHERE name=?', (sport_name,)).fetchone()
    return _from_row(row) if row else None


def get_config_by_id(db, sport_id: int) -> SportConfig | None:
    row = db.execute('SELECT * FROM sport_configs WHERE id=?', (sport_id,)).fetchone()
    return _from_row(row) if row else None


def summary(config: SportConfig) -> dict:
    """Compact representation used by the UI."""
    return {
        'id': config.id,
        'name': config.name,
        'description': config.description,
        'points_system': config.points_system,
        'min_team_size': config.get_team_size_range()[0],
        'max_team_size': config.get_team_size_range()[1],
        'field_type': config.get_field_type(),
        'supports_sets': config.supports_sets(),
    }
