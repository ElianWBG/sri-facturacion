"""Simulador del SRI para desarrollo sin firma electrónica real ni conexión."""
from datetime import datetime

from .ws_sri import ResultadoAutorizacion, ResultadoRecepcion


def simular_recepcion(xml_firmado: bytes) -> ResultadoRecepcion:
    return ResultadoRecepcion(
        estado='RECIBIDA',
        mensajes=[{'tipo': 'SIMULADO', 'mensaje': 'Recepción simulada OK'}],
        raw=None,
    )


def simular_autorizacion(clave_acceso: str, xml_firmado: bytes) -> ResultadoAutorizacion:
    ahora = datetime.now()
    comprobante = xml_firmado.decode('utf-8', errors='ignore')
    xml_autorizado = (
        '<autorizacion>'
        f'<estado>AUTORIZADO</estado>'
        f'<numeroAutorizacion>{clave_acceso}</numeroAutorizacion>'
        f'<fechaAutorizacion>{ahora.isoformat()}</fechaAutorizacion>'
        f'<ambiente>PRUEBAS</ambiente>'
        f'<comprobante><![CDATA[{comprobante}]]></comprobante>'
        '</autorizacion>'
    )
    return ResultadoAutorizacion(
        estado='AUTORIZADO',
        numero_autorizacion=clave_acceso,
        fecha_autorizacion=ahora,
        comprobante=xml_autorizado,
        mensajes=[{'tipo': 'SIMULADO', 'mensaje': 'Autorización simulada OK'}],
        raw=None,
    )
