"""
Secuencial atómico por contribuyente + establecimiento + punto de emisión.
Usa select_for_update() + get_or_create para garantizar que dos workers
de Celery no generen el mismo número para la misma empresa.
"""
from django.db import transaction

from .models import Contribuyente, SecuenciaFactura


@transaction.atomic
def siguiente_secuencial(contribuyente: Contribuyente, establecimiento: str, punto_emision: str) -> str:
    seq, _ = SecuenciaFactura.objects.select_for_update().get_or_create(
        contribuyente=contribuyente,
        establecimiento=establecimiento,
        punto_emision=punto_emision,
        defaults={'ultimo_numero': 0},
    )
    seq.ultimo_numero += 1
    seq.save(update_fields=['ultimo_numero'])
    return str(seq.ultimo_numero).zfill(9)
