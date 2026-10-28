"""Public endpoint contract; routes describe transport, never grant access."""

import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from .common import Rejected, wg_key
from .pki import fingerprint, load_cert

FIELDS = {'schema', 'api_url', 'wireguard_host', 'wireguard_port', 'server_public_key',
          'root_sha256', 'backend_network', 'tunnel_network', 'allowed_ips', 'resources'}


def host(value):
    if not isinstance(value, str) or len(value) > 253:
        raise Rejected('Invalid endpoint host')
    try:
        address = ipaddress.IPv4Address(value)
        if address.is_unspecified or address.is_multicast or address.is_loopback:
            raise ValueError()
        return str(address)
    except ValueError:
        if (re.fullmatch(r'[0-9.]+', value) or not re.fullmatch(
                r'[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?', value)
                or any(not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?', label)
                       for label in value.split('.'))):
            raise Rejected('Invalid endpoint host') from None
        return value.lower()


def port(value):
    if type(value) is not int or not 1 <= value <= 65535:
        raise Rejected('Invalid endpoint port')
    return value


def validate_profile(value):
    try:
        if (not isinstance(value, dict) or type(value.get('schema')) is not int
                or value['schema'] not in (1, 2)
                or set(value) != FIELDS | ({'internet'} if value['schema'] == 2 else set())):
            raise ValueError()
        api = urlsplit(value['api_url'])
        if (api.scheme != 'https' or api.username is not None or api.password is not None
                or api.query or api.fragment or api.path not in ('', '/')
                or any(c.isspace() for c in value['api_url'])):
            raise ValueError()
        api_host = host(api.hostname)
        api_port = port(443 if api.port is None else api.port)
        result = dict(value, api_url=f'https://{api_host}:{api_port}',
                      wireguard_host=host(value['wireguard_host']),
                      wireguard_port=port(value['wireguard_port']))
        wg_key(value['server_public_key'])
        if not re.fullmatch(r'[0-9a-f]{64}', value['root_sha256']):
            raise ValueError()
        if any(not isinstance(value[field], str) for field in ('backend_network', 'tunnel_network')):
            raise ValueError()
        backend = ipaddress.IPv4Network(value['backend_network'])
        tunnel = ipaddress.IPv4Network(value['tunnel_network'])
        # Server registry currently enforces this network; no hidden incompatible migration.
        if tunnel != ipaddress.IPv4Network('10.8.0.0/24') or backend.overlaps(tunnel):
            raise ValueError()
        if (not isinstance(value['allowed_ips'], list) or not 1 <= len(value['allowed_ips']) <= 16
                or any(not isinstance(route, str) for route in value['allowed_ips'])):
            raise ValueError()
        routes = [ipaddress.IPv4Network(x) for x in value['allowed_ips']]
        if value['schema'] == 2:
            internet = value['internet']
            if (not isinstance(internet, dict) or set(internet) != {'mode', 'dns'}
                    or internet['mode'] != 'managed-ipv4'
                    or value['allowed_ips'] != ['0.0.0.0/1', '128.0.0.0/1']
                    or not isinstance(internet['dns'], list) or not 1 <= len(internet['dns']) <= 2):
                raise ValueError()
            # Literal endpoints avoid an unrestricted pre-authentication DNS path.
            for endpoint in (api_host, result['wireguard_host']):
                address = ipaddress.IPv4Address(endpoint)
                if not address.is_global and not address.is_private:
                    raise ValueError()
                if address in tunnel:
                    raise ValueError()
            for resolver in internet['dns']:
                if not isinstance(resolver, str) or not ipaddress.IPv4Address(resolver).is_global:
                    raise ValueError()
        elif len(set(routes)) != len(routes) or any(x.prefixlen != 32 or not x.subnet_of(tunnel) for x in routes):
            raise ValueError()
        if not isinstance(value['resources'], list) or not 1 <= len(value['resources']) <= 16:
            raise ValueError()
        for resource in value['resources']:
            if (not isinstance(resource, dict) or set(resource) != {'name', 'address', 'protocol', 'port'}
                    or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', resource['name'])
                    or resource['protocol'] not in ('tcp', 'udp')
                    or (ipaddress.IPv4Network(resource['address'] + '/32') not in routes
                        if value['schema'] == 1 else ipaddress.IPv4Address(resource['address']) not in tunnel)):
                raise ValueError()
            port(resource['port'])
        return result
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        raise Rejected('Invalid endpoint profile; inspect schema, addresses, routes and resources') from exc


def load_profile(path, trust=None):
    source = Path(path)
    if source.stat().st_size > 32768:
        raise Rejected('Endpoint profile too large')
    result = validate_profile(json.loads(source.read_text(encoding='utf-8-sig')))
    if trust is not None and fingerprint(load_cert(Path(trust).read_bytes())) != result['root_sha256']:
        raise Rejected('Trusted root does not match endpoint profile')
    return result


def check_network_conflicts(profile, addresses, routes):
    """Read-only preflight from an OS snapshot; defaults never prove a safe path."""
    profile = validate_profile(profile)
    tunnel = ipaddress.IPv4Network(profile['tunnel_network'])
    backend = ipaddress.IPv4Network(profile['backend_network'])
    try:
        for value in addresses:
            network = ipaddress.IPv4Interface(value).network
            if network.overlaps(tunnel) or network.overlaps(backend):
                raise Rejected('Local interface overlaps the backend/tunnel network; review allocation')
        for value in routes:
            network = ipaddress.IPv4Network(value)
            if network.prefixlen and network.overlaps(tunnel):
                raise Rejected('Existing route overlaps the tunnel network; inspect other VPNs first')
    except ValueError as exc:
        raise Rejected('Cannot validate local network snapshot') from exc
