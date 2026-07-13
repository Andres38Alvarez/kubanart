"""
Contexto global disponible en todas las plantillas (via TEMPLATES.OPTIONS
en settings.py), para no repetir esta lógica en cada vista.

Calcula en qué "fase" está el proyecto según las regiones que ya tienen
museos cargados en la base de datos, y arma un texto legible tipo
"Phase 1: European Collections" o "Phase 1-2: Europe & North America
Collections" a medida que se agregan territorios nuevos.
"""
from .models import Museum

# Orden en el que se van incorporando las regiones al proyecto.
PHASE_ORDER = ['europe', 'north_america', 'latin_america', 'asia', 'africa']

PHASE_LABELS = {
    'europe': 'Europe',
    'north_america': 'North America',
    'latin_america': 'Latin America',
    'asia': 'Asia',
    'africa': 'Africa',
}


def project_phase(request):
    regions_present = set(
        Museum.objects
        .exclude(region__isnull=True)
        .exclude(region='')
        .values_list('region', flat=True)
        .distinct()
    )

    ordered = [r for r in PHASE_ORDER if r in regions_present]

    if not ordered:
        # Todavía no hay museos con region asignada (o base vacía).
        return {
            'current_phase_label': 'Phase 1: European Collections',
            'current_regions': [],
        }

    names = [PHASE_LABELS[r] for r in ordered]
    collections_label = ' & '.join(names) + ' Collections'
    phase_number = f"Phase 1-{len(ordered)}" if len(ordered) > 1 else "Phase 1"

    return {
        'current_phase_label': f"{phase_number}: {collections_label}",
        'current_regions': ordered,
    }
