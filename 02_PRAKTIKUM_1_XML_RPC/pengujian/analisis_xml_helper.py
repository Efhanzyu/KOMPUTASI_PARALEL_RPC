"""Helper kecil: menghasilkan teks XML hasil marshalling (xmlrpc.client.dumps)."""
import xmlrpc.client


def ambil_xml_dumps(params, methodname):
    if methodname is None:
        return xmlrpc.client.dumps(tuple(params), methodresponse=True)
    return xmlrpc.client.dumps(tuple(params), methodname)
