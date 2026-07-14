"""
Cliente SOAP del SRI usando zeep.

Las URLs de los WSDL dependen del ambiente de CADA contribuyente (1=Pruebas,
2=Producción), por lo que se pasan como parámetros en vez de leer settings.
"""
import base64
import time
from dataclasses import dataclass, field
from pathlib import Path

WSDL = {
    '1': {
        'RECEPCION':    'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl',
        'AUTORIZACION': 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl',
    },
    '2': {
        'RECEPCION':    'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl',
        'AUTORIZACION': 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl',
    },
}


@dataclass
class ResultadoRecepcion:
    estado: str
    mensajes: list = field(default_factory=list)
    raw: object = None


@dataclass
class ResultadoAutorizacion:
    estado: str
    numero_autorizacion: str = ''
    fecha_autorizacion: object = None
    comprobante: str = ''
    mensajes: list = field(default_factory=list)
    raw: object = None


def _client(wsdl: str):
    from zeep import Client, Settings
    from zeep.transports import Transport
    transport = Transport(timeout=30, operation_timeout=30)
    return Client(wsdl, settings=Settings(strict=False, xml_huge_tree=True), transport=transport)


def _mensajes(comprobante) -> list:
    salida = []
    try:
        for c in comprobante.mensajes.mensaje:
            salida.append({
                'identificador':        getattr(c, 'identificador', ''),
                'mensaje':              getattr(c, 'mensaje', ''),
                'informacionAdicional': getattr(c, 'informacionAdicional', ''),
                'tipo':                 getattr(c, 'tipo', ''),
            })
    except (AttributeError, TypeError):
        pass
    return salida


def enviar_recepcion(xml_firmado: bytes, *, ambiente: str = '1', simulado: bool = False) -> ResultadoRecepcion:
    if simulado:
        from . import simulador
        return simulador.simular_recepcion(xml_firmado)

    client = _client(WSDL[ambiente]['RECEPCION'])
    xml_b64 = base64.b64encode(xml_firmado)
    respuesta = client.service.validarComprobante(xml_b64)
    estado = getattr(respuesta, 'estado', 'DEVUELTA')

    mensajes = []
    try:
        for comp in respuesta.comprobantes.comprobante:
            mensajes.extend(_mensajes(comp))
    except (AttributeError, TypeError):
        pass

    return ResultadoRecepcion(estado=estado, mensajes=mensajes, raw=respuesta)


def consultar_autorizacion(clave_acceso: str, *, ambiente: str = '1', simulado: bool = False, comprobantes_dir: str = '') -> ResultadoAutorizacion:
    if simulado:
        from . import simulador
        xml_path = Path(comprobantes_dir) / f'{clave_acceso}.xml' if comprobantes_dir else None
        xml_firmado = xml_path.read_bytes() if (xml_path and xml_path.exists()) else b''
        return simulador.simular_autorizacion(clave_acceso, xml_firmado)

    client = _client(WSDL[ambiente]['AUTORIZACION'])
    respuesta = client.service.autorizacionComprobante(clave_acceso)

    try:
        aut = respuesta.autorizaciones.autorizacion[0]
    except (AttributeError, IndexError, TypeError):
        return ResultadoAutorizacion(estado='EN PROCESO', raw=respuesta)

    return ResultadoAutorizacion(
        estado=getattr(aut, 'estado', 'NO AUTORIZADO'),
        numero_autorizacion=getattr(aut, 'numeroAutorizacion', '') or '',
        fecha_autorizacion=getattr(aut, 'fechaAutorizacion', None),
        comprobante=getattr(aut, 'comprobante', '') or '',
        mensajes=_mensajes(aut),
        raw=respuesta,
    )


def esperar_autorizacion(
    clave_acceso: str,
    *,
    ambiente: str = '1',
    simulado: bool = False,
    comprobantes_dir: str = '',
    intentos: int = 6,
    espera_seg: int = 5,
) -> ResultadoAutorizacion:
    ultimo = ResultadoAutorizacion(estado='EN PROCESO')
    for _ in range(intentos):
        ultimo = consultar_autorizacion(
            clave_acceso, ambiente=ambiente, simulado=simulado, comprobantes_dir=comprobantes_dir
        )
        if ultimo.estado != 'EN PROCESO':
            return ultimo
        time.sleep(espera_seg)
    return ultimo
