"""Sport catalog and variant rules read from the database.

`SportConfig` is the parent (Calcio, Basket, ...); `VariantConfig` carries the
rules that actually drive a tournament (Calcio a 5, Basket 3x3, ...).
"""

import json
from dataclasses import dataclass, field
from typing import Any


def _load_json(value: str | None) -> dict[str, Any]:
    try:
        parsed = json.loads(value or '{}')
    except (TypeError, ValueError):
        parsed = {}
    return parsed if isinstance(parsed, dict) else {}


@dataclass(frozen=True)
class VariantConfig:
    """Rules for one selectable variant of a sport."""

    id: int
    sport_id: int
    sport_name: str
    slug: str
    name: str
    description: str
    participant_kind: str
    sort_order: int
    rules: dict[str, Any] = field(default_factory=dict)
    regulation: str = ''

    def get_team_size_range(self) -> tuple[int, int]:
        return (int(self.rules.get('min_lineup', 1)),
                int(self.rules.get('max_roster', 1)))

    @property
    def players_on_field(self) -> int:
        return int(self.rules.get('players_on_field', 1))

    @property
    def min_lineup(self) -> int:
        return int(self.rules.get('min_lineup', 1))

    @property
    def max_roster(self) -> int:
        return int(self.rules.get('max_roster', 1))

    @property
    def match_duration(self) -> int:
        return int(self.rules.get('match_duration', 20))

    @property
    def scoring_mode(self) -> str:
        return str(self.rules.get('scoring_mode', 'points'))

    @property
    def score_label(self) -> str:
        return str(self.rules.get('score_label', 'punti'))

    @property
    def draw_allowed(self) -> bool:
        return bool(self.rules.get('draw_allowed', True))

    @property
    def supports_sets(self) -> bool:
        return self.scoring_mode == 'sets'

    @property
    def sets_to_win(self) -> int | None:
        value = self.rules.get('sets_to_win')
        return int(value) if value is not None else None

    @property
    def max_sets(self) -> int | None:
        value = self.rules.get('max_sets')
        return int(value) if value is not None else None

    @property
    def points_per_set(self) -> int | None:
        value = self.rules.get('points_per_set')
        return int(value) if value is not None else None

    @property
    def tiebreak_points(self) -> int | None:
        value = self.rules.get('tiebreak_points')
        return int(value) if value is not None else None

    @property
    def win_by_two(self) -> bool:
        return bool(self.rules.get('win_by_two', False))

    @property
    def max_points(self) -> int | None:
        value = self.rules.get('max_points')
        return int(value) if value is not None else None

    @property
    def standings(self) -> dict[str, int | None]:
        value = self.rules.get('standings') or {}
        return value if isinstance(value, dict) else {}

    @property
    def default_tie_breaker(self) -> str:
        return str(self.rules.get('default_tie_breaker', 'goal_difference'))

    def get_field_type(self) -> str:
        return str(self.rules.get('surface') or
                   self.rules.get('court_type') or
                   self.rules.get('field_type') or 'campo')


@dataclass(frozen=True)
class SportConfig:
    """A parent sport with its selectable variants."""

    id: int
    name: str
    description: str
    points_system: str
    sort_order: int = 0
    rules: dict[str, Any] = field(default_factory=dict)
    variants: tuple[VariantConfig, ...] = ()

    def default_variant(self, participant_kind: str | None = None) -> VariantConfig | None:
        candidates = self.variants
        if participant_kind:
            matching = tuple(v for v in candidates
                             if v.participant_kind == participant_kind)
            if matching:
                candidates = matching
        return sorted(candidates, key=lambda v: (v.sort_order, v.id))[0] \
            if candidates else None


def _variant_from_row(row) -> VariantConfig:
    return VariantConfig(
        id=row['variant_id'],
        sport_id=row['sport_id'],
        sport_name=row['sport_name'],
        slug=row['slug'],
        name=row['variant_name'],
        description=row['variant_description'],
        participant_kind=row['participant_kind'],
        sort_order=row['variant_sort_order'],
        rules=_load_json(row['rules']),
        regulation=row['regulation'] or '',
    )


def _variants_by_sport(db) -> dict[int, list[VariantConfig]]:
    result: dict[int, list[VariantConfig]] = {}
    rows = db.execute(
        'SELECT v.id AS variant_id, v.sport_id, s.name AS sport_name, v.slug, '
        '       v.name AS variant_name, v.description AS variant_description, '
        '       v.participant_kind, v.sort_order AS variant_sort_order, '
        '       v.rules, v.regulation '
        'FROM sport_variants v JOIN sport_configs s ON s.id = v.sport_id '
        'ORDER BY s.sort_order, s.id, v.sort_order, v.id'
    )
    for row in rows:
        result.setdefault(row['sport_id'], []).append(_variant_from_row(row))
    return result


def _sport_from_row(row, variants: list[VariantConfig]) -> SportConfig:
    return SportConfig(
        id=row['id'],
        name=row['name'],
        description=row['description'],
        points_system=row['points_system'],
        sort_order=row['sort_order'],
        rules=_load_json(row['rules']),
        variants=tuple(variants),
    )


def list_sports(db) -> list[SportConfig]:
    """Return every parent sport with its variants, in catalog order."""
    variants = _variants_by_sport(db)
    rows = db.execute('SELECT * FROM sport_configs ORDER BY sort_order, name, id')
    return [_sport_from_row(row, variants.get(row['id'], [])) for row in rows]


def get_sport(db, name: str) -> SportConfig | None:
    row = db.execute('SELECT * FROM sport_configs WHERE name=?', (name,)).fetchone()
    if row is None:
        return None
    variants = _variants_by_sport(db).get(row['id'], [])
    return _sport_from_row(row, variants)


def get_sport_by_id(db, sport_id: int) -> SportConfig | None:
    row = db.execute('SELECT * FROM sport_configs WHERE id=?', (sport_id,)).fetchone()
    if row is None:
        return None
    variants = _variants_by_sport(db).get(row['id'], [])
    return _sport_from_row(row, variants)


def _variant_query(db, where: str, params):
    row = db.execute(
        'SELECT v.id AS variant_id, v.sport_id, s.name AS sport_name, v.slug, '
        '       v.name AS variant_name, v.description AS variant_description, '
        '       v.participant_kind, v.sort_order AS variant_sort_order, '
        '       v.rules, v.regulation '
        'FROM sport_variants v JOIN sport_configs s ON s.id = v.sport_id '
        f'WHERE {where}', params
    ).fetchone()
    return _variant_from_row(row) if row else None


def get_variant(db, sport_name: str, slug: str) -> VariantConfig | None:
    return _variant_query(db, 's.name=? AND v.slug=?', (sport_name, slug))


def get_variant_by_slug(db, slug: str) -> VariantConfig | None:
    return _variant_query(db, 'v.slug=?', (slug,))


def get_variant_by_id(db, variant_id: int) -> VariantConfig | None:
    return _variant_query(db, 'v.id=?', (variant_id,))


def variant_summary(variant: VariantConfig) -> dict:
    """Compact representation used by lists and the wizard."""
    return {
        'id': variant.id,
        'sport_id': variant.sport_id,
        'sport': variant.sport_name,
        'slug': variant.slug,
        'name': variant.name,
        'description': variant.description,
        'participant_kind': variant.participant_kind,
        'sort_order': variant.sort_order,
        'players_on_field': variant.players_on_field,
        'min_lineup': variant.min_lineup,
        'max_roster': variant.max_roster,
        'match_duration': variant.match_duration,
        'scoring_mode': variant.scoring_mode,
        'score_label': variant.score_label,
        'draw_allowed': variant.draw_allowed,
        'supports_sets': variant.supports_sets,
        'sets_to_win': variant.sets_to_win,
        'max_sets': variant.max_sets,
        'points_per_set': variant.points_per_set,
        'tiebreak_points': variant.tiebreak_points,
        'win_by_two': variant.win_by_two,
        'max_points': variant.max_points,
        'standings': variant.standings,
        'default_tie_breaker': variant.default_tie_breaker,
        'surface': variant.get_field_type(),
    }


def variant_detail(variant: VariantConfig) -> dict:
    return {**variant_summary(variant), 'rules': variant.rules,
            'regulation': variant.regulation}


def summary(sport: SportConfig) -> dict:
    """Parent sport with nested variants, used by `/api/sports`."""
    default = sport.default_variant('team') or sport.default_variant()
    return {
        'id': sport.id,
        'name': sport.name,
        'description': sport.description,
        'points_system': sport.points_system,
        'sort_order': sport.sort_order,
        'min_team_size': default.min_lineup if default else 1,
        'max_team_size': default.max_roster if default else 11,
        'field_type': default.get_field_type() if default else 'campo',
        'supports_sets': default.supports_sets if default else False,
        'default_variant': default.slug if default else None,
        'variants': [variant_summary(v) for v in sport.variants],
    }


# Backwards-compatible helpers for callers that only know a sport name.
def list_configs(db) -> list[SportConfig]:
    return list_sports(db)


def get_config(db, sport_name: str) -> SportConfig | None:
    return get_sport(db, sport_name)


def get_config_by_id(db, sport_id: int) -> SportConfig | None:
    return get_sport_by_id(db, sport_id)
