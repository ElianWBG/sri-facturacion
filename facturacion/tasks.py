"""
Tarea Celery: orquesta el ciclo completo de emisión de una factura.

    PENDIENTE → (clave+XML) → (firma XAdES-BES) → recepción SRI
       └→ ENVIADO → autorización SRI → AUTORIZADO → RIDE + correo

La tarea lee toda la config del emisor desde factura.contribuyente,
por lo que es completamente agnóstica de cuál empresa está facturando.
"""
import logging
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Factura
from .sri.clave_acceso import generar_clave_acceso
from .sri.correo import enviar_comprobante
from .sri.firma import firmar_comprobante
from .sri.ride import generar_ride
from .sri.ws_sri import enviar_recepcion, esperar_autorizacion
from .sri.xml_builder import construir_xml_factura

logger = logging.getLogger(__name__)


def _items_normalizados(factura: Factura) -> list[dict]:
    return [
        {
            'codigo':          it['codigo'],
            'descripcion':     it['descripcion'],
            'cantidad':        it['cantidad'],
            'precio_unitario': it['precio_unitario'],
            'descuento':       it.get('descuento', 0),
            'codigo_iva':      it.get('codigo_iva', '2'),
        }
        for it in factura.payload.get('items', [])
    ]


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def emitir_factura(self, factura_id: int):
    factura = Factura.objects.select_related('contribuyente').get(pk=factura_id)
    contribuyente = factura.contribuyente

    factura.intentos += 1
    factura.save(update_fields=['intentos'])

    emisor  = contribuyente.as_emisor_dict()
    items   = _items_normalizados(factura)
    out_dir = Path(settings.COMPROBANTES_DIR) / contribuyente.ruc
    out_dir.mkdir(parents=True, exist_ok=True)

    # Ruta al .p12 (puede ser None si está en modo simulado)
    p12_path = contribuyente.firma_p12.path if contribuyente.firma_p12 else ''
    p12_password = contribuyente.clave_firma

    try:
        # 1) Clave de acceso (49 dígitos) + XML sin firmar
        clave = generar_clave_acceso(
            fecha_emision=timezone.localdate(),
            tipo_comprobante='01',
            ruc=contribuyente.ruc,
            ambiente=factura.ambiente,
            establecimiento=factura.establecimiento,
            punto_emision=factura.punto_emision,
            secuencial=factura.secuencial,
        )
        factura.clave_acceso = clave
        factura.save(update_fields=['clave_acceso'])

        xml_bytes = construir_xml_factura(
            emisor=emisor, factura=factura, items=items, clave_acceso=clave
        )

        # 2) Firma XAdES-BES (real o simulada según si hay .p12)
        xml_firmado = firmar_comprobante(
            xml_bytes,
            simulado=contribuyente.simulado,
            p12_path=p12_path,
            p12_password=p12_password,
        )
        xml_path = out_dir / f'{clave}.xml'
        xml_path.write_bytes(xml_firmado)
        factura.xml_path = str(xml_path)
        factura.save(update_fields=['xml_path'])

        # 3) Recepción en el SRI
        recepcion = enviar_recepcion(xml_firmado, ambiente=contribuyente.ambiente, simulado=contribuyente.simulado)
        if recepcion.estado != 'RECIBIDA':
            factura.marcar(Factura.Estado.DEVUELTO, mensaje=str(recepcion.mensajes))
            return {'factura': factura_id, 'estado': factura.estado}

        factura.marcar(Factura.Estado.ENVIADO)

        # 4) Autorización (poll hasta AUTORIZADO)
        autorizacion = esperar_autorizacion(
            clave,
            ambiente=contribuyente.ambiente,
            simulado=contribuyente.simulado,
            comprobantes_dir=str(out_dir),
            intentos=6,
            espera_seg=5,
        )
        if autorizacion.estado != 'AUTORIZADO':
            factura.marcar(Factura.Estado.RECHAZADO, mensaje=str(autorizacion.mensajes) or autorizacion.estado)
            return {'factura': factura_id, 'estado': factura.estado}

        xml_aut_path = out_dir / f'{clave}_autorizado.xml'
        if autorizacion.comprobante:
            xml_aut_path.write_text(autorizacion.comprobante, encoding='utf-8')
            factura.xml_autorizado_path = str(xml_aut_path)

        factura.numero_autorizacion = autorizacion.numero_autorizacion or clave
        factura.fecha_autorizacion = timezone.now()
        factura.estado = Factura.Estado.AUTORIZADO
        factura.save()

        # 5) RIDE (PDF + QR)
        pdf_path = generar_ride(
            emisor=emisor,
            factura=factura,
            items=items,
            destino=out_dir / f'{clave}.pdf',
        )
        factura.pdf_path = str(pdf_path)
        factura.save(update_fields=['pdf_path'])

        # 6) Correo al cliente (fallo aislado: no reintenta todo el flujo)
        try:
            enviar_comprobante(
                factura=factura,
                xml_path=factura.xml_autorizado_path or factura.xml_path,
                pdf_path=factura.pdf_path,
            )
        except Exception as mail_exc:
            logger.exception('Error enviando comprobante por correo para factura %s: %s', factura_id, mail_exc)

        return {'factura': factura_id, 'estado': factura.estado}

    except Exception as exc:
        logger.exception('Error emitiendo factura %s', factura_id)
        factura.mensaje_sri = f'{type(exc).__name__}: {exc}'
        factura.save(update_fields=['mensaje_sri'])
        raise self.retry(exc=exc)
