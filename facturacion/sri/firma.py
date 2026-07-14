"""Firma electrónica XAdES-BES del XML de la factura."""


def firmar_comprobante(xml_bytes: bytes, *, simulado: bool, p12_path: str = '', p12_password: str = '') -> bytes:
    if simulado:
        return _firma_simulada(xml_bytes)
    return firmar_xml_xades_bes(xml_bytes, p12_path=p12_path, p12_password=p12_password)


def _firma_simulada(xml_bytes: bytes) -> bytes:
    stub = (
        b'<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Id="SimulacionBES">'
        b'<ds:SignedInfo><ds:SignatureValue>FIRMA_SIMULADA</ds:SignatureValue></ds:SignedInfo>'
        b'</ds:Signature>'
    )
    if b'</factura>' in xml_bytes:
        return xml_bytes.replace(b'</factura>', stub + b'</factura>')
    return xml_bytes + stub


def _cargar_p12(p12_path: str, password: str):
    from cryptography.hazmat.primitives.serialization import pkcs12
    with open(p12_path, 'rb') as fh:
        data = fh.read()
    key, cert, extra = pkcs12.load_key_and_certificates(data, password.encode('utf-8'))
    return key, cert, extra or []


def firmar_xml_xades_bes(xml_bytes: bytes, *, p12_path: str, p12_password: str) -> bytes:
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
    from lxml import etree
    import xmlsig
    import xades

    root = etree.fromstring(xml_bytes)
    signature = xmlsig.template.create(
        c14n_method=xmlsig.constants.TransformInclC14N,
        sign_method=xmlsig.constants.TransformRsaSha1,
        name='Signature',
    )
    root.append(signature)

    ref = xmlsig.template.add_reference(signature, xmlsig.constants.TransformSha1, uri='#comprobante')
    xmlsig.template.add_transform(ref, xmlsig.constants.TransformEnveloped)
    xmlsig.template.add_reference(signature, xmlsig.constants.TransformSha1, uri='', name='KeyInfo')
    ki = xmlsig.template.ensure_key_info(signature)
    x509 = xmlsig.template.add_x509_data(ki)
    xmlsig.template.x509_data_add_certificate(x509)

    qualifying = xades.template.create_qualifying_properties(signature)
    props = xades.template.create_signed_properties(qualifying, name='SignedProperties')
    xades.template.add_claimed_role(props, 'Emisor')

    ctx = xmlsig.SignatureContext()
    key, cert, _ = _cargar_p12(p12_path, p12_password)

    ctx.x509 = cert
    ctx.private_key = key

    policy = xades.policy.GenericPolicyId('', 'XAdES-BES', xmlsig.constants.TransformSha1)
    ctx.sign(signature)
    policy.calculate_certificate(props, cert)
    policy.sign(signature, key, cert)

    return etree.tostring(root, encoding='UTF-8', xml_declaration=True)
