import requests_cache
from logzero import logger
from typing import Optional
from dataclasses import dataclass
from collections import UserList
from xml.etree import ElementTree
from urllib.parse import urlparse
from urllib3 import disable_warnings

disable_warnings()


class InvalidParameters(Exception):
    """Raised when the GNS3 server has genererated an error due to the parameters sent in the request."""
    pass


class ObjectDoesNotExist(Exception):
    """Raised when the GNS3 object does not exist"""
    pass


class ObjectAlreadyExists(Exception):
    """Raised when the GNS3 object already exists"""
    pass


class Server(requests_cache.CachedSession):
    """
    This class specifies how to connect to a GNS3 server: the base URL, the credentials, and if SSL must be checked.
    """

    def __init__(self, base_url: str = None, username: str = None, password: str = None, verify: bool = False) -> None:
        super(Server, self).__init__()
        self.base_url = base_url
        if username:
            self.auth = (username, password)
        self.verify = verify
        self.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        self.templates = TemplateList(server=self)
        self.projects = ProjectList(server=self)
        self.cache.clear()

    def _prepend_base_url(self, url: str) -> str:
        """Return the URL prepended with a base URL"""
        o = urlparse(self.base_url)
        path = o.path + '/' + url
        while '//' in path:
            path = path.replace('//', '/')
        o = o._replace(path=path)  # noqa
        return o.geturl()

    def request(self, method: str, url: str, prepend_base_url: bool = True, *args, **kwargs):
        """Extends original requests.request with optional URL prepending"""
        if prepend_base_url:
            url = self._prepend_base_url(url)
        logger.debug(f'Request sent: {method} {url}')
        r = super(Server, self).request(method, url, *args, **kwargs)
        logger.debug(f'Request status: {r.status_code} {r.reason}')
        return r

    def version(self) -> dict:
        """Returns GNS3 server version"""
        return self.get(url="/version").json()


@dataclass
class BaseObjectMetadata:
    _READONLY_ATTRIBUTES = ()

    name: Optional[str] = None

    def update(self, data_dict: dict):
        """Updates attributes from dict"""
        for k, v in data_dict.items():
            if k in vars(self):
                self.__setattr__(k, v)
        return self

    def dict(self, include_ro: bool = False) -> dict:
        """Returns a dict from attributes"""
        exclude_attrs = ()
        if not include_ro:
            exclude_attrs = self._READONLY_ATTRIBUTES
        return {
            k: v
            for k, v in vars(self).items()
            if v is not None and k not in exclude_attrs and k[0] != '_'
        }

    @staticmethod
    def _diff_dict(local_object: dict, remote_object: dict) -> dict:
        """Returns a recursive dict diff between local_object and remote_object dicts"""
        result = dict()
        remote_object_params = {k: v for k, v in remote_object.items() if v is not None}
        local_object_params = {
            k: v
            for k, v in local_object.items()
            if v is not None and k[0] != '_'
        }
        for k, v in local_object_params.items():
            if k not in remote_object_params:
                result[k] = local_object_params[k]
            if k in remote_object_params and remote_object_params[k] != local_object_params[k]:
                result[k] = local_object_params[k]
                if isinstance(remote_object_params[k], dict) and isinstance(local_object_params[k], dict):
                    result[k] = BaseObjectMetadata._diff_dict(local_object_params[k], remote_object_params[k])
                    if not result[k]:
                        del result[k]
        return result

    def diff(self, remote_object: dict) -> dict:
        """Returns a dict diff between remote_object and instance (local_object)"""
        local_object = {
            k: v
            for k, v in vars(self).items()
            if v is not None and k[0] != '_'
        }
        return self._diff_dict(local_object, remote_object)


@dataclass
class TemplateMetadata(BaseObjectMetadata):
    """Template Metadata

    JSON example:

    {
        'adapter_type': 'e1000',
        'adapters': 1,
        'bios_image': '',
        'boot_priority': 'c',
        'builtin': False,
        'category': 'guest',
        'cdrom_image': '',
        'compute_id': 'local',
        'console_auto_start': False,
        'console_type': 'telnet',
        'cpu_throttling': 0,
        'cpus': 1,
        'create_config_disk': False,
        'custom_adapters': [],
        'default_name_format': '{name}-{0}',
        'first_port_name': '',
        'hda_disk_image': '',
        'hda_disk_interface': 'none',
        'hdb_disk_image': '',
        'hdb_disk_interface': 'none',
        'hdc_disk_image': '',
        'hdc_disk_interface': 'none',
        'hdd_disk_image': '',
        'hdd_disk_interface': 'none',
        'initrd': '',
        'kernel_command_line': '',
        'kernel_image': '',
        'legacy_networking': False,
        'linked_clone': True,
        'mac_address': '',
        'name': 'test_template',
        'on_close': 'power_off',
        'options': '',
        'platform': 'i386',
        'port_name_format': 'Ethernet{0}',
        'port_segment_size': 0,
        'process_priority': 'normal',
        'qemu_path': '',
        'ram': 256,
        'replicate_network_connection_state': True,
        'symbol': ':/symbols/qemu_guest.svg',
        'template_id': 'b43cf702-ba26-45bd-8eae-339e6217565b',
        'template_type': 'qemu',
        'usage': ''
    }
    """
    template_id: Optional[str] = None
    template_type: Optional[str] = None

    adapter_type: Optional[str] = None
    adapters: Optional[int] = None
    bios_image: Optional[str] = None
    boot_priority: Optional[str] = None
    builtin: Optional[bool] = None
    category: Optional[str] = None
    cdrom_image: Optional[str] = None
    compute_id: Optional[str] = "local"
    console_auto_start: Optional[bool] = None
    console_http_path: Optional[str] = None
    console_http_port: Optional[str] = None
    console_resolution: Optional[str] = None
    console_type: Optional[str] = None
    cpu_throttling: Optional[int] = None
    cpus: Optional[int] = None
    create_config_disk: Optional[bool] = None
    custom_adapters: Optional[list] = None
    default_name_format: Optional[str] = None
    environment: Optional[str] = None
    extra_hosts: Optional[str] = None
    extra_volumes: Optional[list] = None
    first_port_name: Optional[str] = None
    hda_disk_image: Optional[str] = None
    hda_disk_interface: Optional[str] = None
    hdb_disk_image: Optional[str] = None
    hdb_disk_interface: Optional[str] = None
    hdc_disk_image: Optional[str] = None
    hdc_disk_interface: Optional[str] = None
    hdd_disk_image: Optional[str] = None
    hdd_disk_interface: Optional[str] = None
    image: Optional[str] = None
    initrd: Optional[str] = None
    kernel_command_line: Optional[str] = None
    kernel_image: Optional[str] = None
    legacy_networking: Optional[bool] = None
    linked_clone: Optional[bool] = None
    mac_address: Optional[str] = None
    on_close: Optional[str] = None
    options: Optional[str] = None
    platform: Optional[str] = None
    properties: Optional[dict] = None
    port_name_format: Optional[str] = None
    port_segment_size: Optional[int] = None
    ports_mapping: Optional[list] = None
    process_priority: Optional[str] = None
    qemu_path: Optional[str] = None
    ram: Optional[int] = None
    replicate_network_connection_state: Optional[bool] = None
    symbol: Optional[str] = None
    start_command: Optional[str] = None
    usage: Optional[str] = None


@dataclass
class ProjectMetadata(BaseObjectMetadata):
    """Project Metadata

    JSON example:
    {
        'auto_close': False,
        'auto_open': False,
        'auto_start': False,
        'drawing_grid_size': 25,
        'filename': 'test_project.gns3',
        'grid_size': 75,
        'name': 'test_project',
        'path': '/opt/gns3/projects/51424064-6ee6-49b3-8158-ad27a59eaaee',
        'project_id': '51424064-6ee6-49b3-8158-ad27a59eaaee',
        'scene_height': 1000,
        'scene_width': 2000,
        'show_grid': False,
        'show_interface_labels': False,
        'show_layers': False,
        'snap_to_grid': False,
        'status': 'opened',
        'supplier': None,
        'variables': None,
        'zoom': 100
    }
    """
    _READONLY_ATTRIBUTES = 'status', 'project_id', 'filename'

    project_id: Optional[str] = None

    auto_close: Optional[bool] = None
    auto_open: Optional[bool] = None
    auto_start: Optional[bool] = None
    drawing_grid_size: Optional[int] = None
    filename: Optional[str] = None
    grid_size: Optional[int] = None
    path: Optional[str] = None
    scene_height: Optional[int] = None
    scene_width: Optional[int] = None
    show_grid: Optional[bool] = None
    show_interface_labels: Optional[bool] = None
    show_layers: Optional[bool] = None
    snap_to_grid: Optional[bool] = None
    status: Optional[str] = None
    supplier: Optional[dict] = None
    variables: Optional[dict] = None
    zoom: Optional[int] = None


@dataclass
class DrawingMetadata(BaseObjectMetadata):
    """Drawing Metadata

    JSON example:
    {
        'drawing_id': '4bcd27fc-e61a-4e26-80bd-689826830ccd',
        'locked': False,
        'project_id': '469ecdd2-b41b-4a2e-ac50-2da823481503',
        'rotation': 0,
        'svg': '<svg height="100" width="100" name="test_drawing">
                  <rect fill="#ebecff" fill-opacity="1.0" height="100" width="100" />
                </svg>',
        'x': 0,
        'y': 0,
        'z': 2
    }
    """
    _READONLY_ATTRIBUTES = 'name', 'project_id'

    drawing_id: Optional[str] = None

    locked: Optional[bool] = None
    project_id: Optional[str] = None
    rotation: Optional[int] = None
    svg: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    z: Optional[int] = None

    def _import_svg_field(self) -> None:
        if self.svg:
            xml = ElementTree.fromstring(self.svg)
            if 'name' in xml.attrib and xml.attrib['name']:
                self.name = xml.attrib.pop('name')
                self.svg = ElementTree.tostring(xml, encoding='unicode')

    def _export_svg_field(self) -> None:
        xml = ElementTree.fromstring(self.svg)
        if self.name:
            xml.attrib['name'] = self.name
            self.svg = ElementTree.tostring(xml, encoding='unicode')

    def update(self, data_dict: dict):
        super(DrawingMetadata, self).update(data_dict)
        self._import_svg_field()
        return self

    def dict(self, include_ro: bool = False) -> dict:
        if not include_ro:
            self._export_svg_field()
        return super(DrawingMetadata, self).dict(include_ro)


@dataclass
class NodeMetadata(BaseObjectMetadata):
    """

    JSON example:
    {
        'command_line': '',
        'compute_id': 'local',
        'console': 5000,
        'console_auto_start': False,
        'console_host': '0.0.0.0',
        'console_type': 'telnet',
        'custom_adapters': [],
        'first_port_name': '',
        'height': 59,
        'label':
            {
                'rotation': 0,
                'style': None,
                'text': 'test_template-1',
                'x': None,
                'y': -40
            },
        'locked': False,
        'name': 'test_template-1',
        'node_directory': '/opt/gns3/projects/87c42844-b1b1-471d-9b0d-643093372568/project-files/qemu/\
            40cdf193-b2d5-461f-ba19-6596c0cd602f',
        'node_id': '40cdf193-b2d5-461f-ba19-6596c0cd602f',
        'node_type': 'qemu',
        'port_name_format': 'Ethernet{0}',
        'port_segment_size': 0,
        'ports':
            [
                {
                    'adapter_number': 0,
                    'adapter_type': 'e1000',
                    'data_link_types':
                        {
                            'Ethernet': 'DLT_EN10MB'
                        },
                    'link_type': 'ethernet',
                    'mac_address': '0c:cd:f1:93:00:00',
                    'name': 'Ethernet0',
                    'port_number': 0,
                    'short_name': 'e0'
                }
            ],
        'project_id': '87c42844-b1b1-471d-9b0d-643093372568',
        'properties':
            {
                'adapter_type': 'e1000',
                'adapters': 1,
                'bios_image': '',
                'bios_image_md5sum': None,
                'boot_priority': 'c',
                'cdrom_image': '',
                'cdrom_image_md5sum': None,
                'cpu_throttling': 0,
                'cpus': 1,
                'create_config_disk': False,
                'hda_disk_image': '',
                'hda_disk_image_md5sum': None,
                'hda_disk_interface': 'none',
                'hdb_disk_image': '',
                'hdb_disk_image_md5sum': None,
                'hdb_disk_interface': 'none',
                'hdc_disk_image': '',
                'hdc_disk_image_md5sum': None,
                'hdc_disk_interface': 'none',
                'hdd_disk_image': '',
                'hdd_disk_image_md5sum': None,
                'hdd_disk_interface': 'none',
                'initrd': '',
                'initrd_md5sum': None,
                'kernel_command_line': '',
                'kernel_image': '',
                'kernel_image_md5sum': None,
                'legacy_networking': False,
                'linked_clone': True,
                'mac_address': '0c:cd:f1:93:00:00',
                'on_close': 'power_off',
                'options': '',
                'platform': 'i386',
                'process_priority': 'normal',
                'qemu_path': '/bin/qemu-system-i386',
                'ram': 256,
                'replicate_network_connection_state': True,
                'usage': ''
            },
        'status': 'stopped',
        'symbol': ':/symbols/qemu_guest.svg',
        'template_id': '45710015-abe8-46f5-8e38-b7618fe20ef8',
        'width': 65,
        'x': 0,
        'y': 0,
        'z': 1
    }
    """
    _READONLY_ATTRIBUTES = 'command_line', 'console', 'console_host', 'height', 'node_directory', 'node_id', 'ports', \
                           'project_id', 'status', 'template_id', 'width'

    node_id: Optional[str] = None
    node_type: Optional[str] = None

    command_line: Optional[str] = None
    compute_id: Optional[str] = 'local'
    console: Optional[int] = None
    console_auto_start: Optional[bool] = None
    console_host: Optional[str] = None
    console_type: Optional[str] = None
    custom_adapters: Optional[list] = None
    first_port_name: Optional[str] = None
    height: Optional[int] = None
    label: Optional[dict] = None
    locked: Optional[bool] = None
    node_directory: Optional[str] = None
    port_name_format: Optional[str] = None
    port_segment_size: Optional[int] = None
    ports: Optional[list] = None
    project_id: Optional[str] = None
    properties: Optional[dict] = None
    status: Optional[str] = None
    symbol: Optional[str] = None
    template_id: Optional[str] = None
    width: Optional[int] = None
    x: Optional[int] = 0
    y: Optional[int] = 0
    z: Optional[int] = None


@dataclass
class LinkMetadata(BaseObjectMetadata):
    """Link Metadata

    JSON example:
    {
        "capture_compute_id": null,
        "capture_file_name": null,
        "capture_file_path": null,
        "capturing": false,
        "filters": {},
        "link_id": "bb2f19d4-5061-4e45-84d2-c931cd1bf39c",
        "link_style": {},
        "link_type": "ethernet",
        "nodes":
            [
                {
                    "adapter_number": 0,
                    "label":
                    {
                        "rotation": 0,
                        "style": "font-size: 10; font-style: Verdana",
                        "text": "e0",
                        "x": 82,
                        "y": 23
                    },
                    "node_id": "5cfdc2a2-0ec3-4b02-abe9-efbefa74eaac",
                    "port_number": 0
                },
                {
                    "adapter_number": 0,
                    "label":
                    {
                        "rotation": 0,
                        "style": "font-size: 10; font-style: Verdana",
                        "text": "e0",
                        "x": -18,
                        "y": 35
                    },
                    "node_id": "3f6fcd32-d18b-42ef-8ce1-f4f760f91e28",
                    "port_number": 0
                }
            ],
        "project_id": "55b54174-0e63-48c8-97c7-bb3a5c18aa4e",
        "suspend": false
    }
    """

    _READONLY_ATTRIBUTES = 'capture_compute_id', 'capture_file_name', 'capture_file_path', 'capturing', 'link_id', \
                           'project_id'
    _project = None

    link_id: Optional[str] = None
    link_type: Optional[str] = None

    capture_compute_id: Optional[str] = None
    capture_file_name: Optional[str] = None
    capture_file_path: Optional[str] = None
    capturing: Optional[bool] = None
    filters: Optional[dict] = None
    link_style: Optional[dict] = None
    nodes: Optional[list[dict]] = None
    project_id: Optional[str] = None
    suspend: Optional[bool] = None

    def _import_nodes_field(self) -> None:
        if self.nodes:
            for node in self.nodes:
                if 'node_id' in node:
                    n = Node(project=self._project, node_id=node['node_id'])
                    n.read()
                    node['node'] = n
                    del node['node_id']

    def _export_nodes_field(self) -> None:
        if self.nodes:
            for node in self.nodes:
                if 'node' in node:
                    node['node_id'] = node['node'].id
                    del node['node']

    def update(self, data_dict: dict):
        super(LinkMetadata, self).update(data_dict)
        self._import_nodes_field()
        return self

    def dict(self, include_ro: bool = False) -> dict:
        if not include_ro:
            self._export_nodes_field()
        return super(LinkMetadata, self).dict(include_ro)

    def diff(self, remote_object: dict) -> dict:
        result = super(LinkMetadata, self).diff(remote_object)
        if 'nodes' in result:
            del result['nodes']
        if not Link.are_link_ends_the_same(remote_object['nodes'], self.nodes):
            result['nodes'] = self.nodes
        return result


class BaseObject:
    _MetadataClass = BaseObjectMetadata

    def __init__(self, **kwargs) -> None:
        self.metadata = self._MetadataClass(**kwargs)

    def __repr__(self):
        return self.metadata.__repr__().replace('Metadata(', '(')

    @property
    def _endpoint_url(self) -> str:
        """Property to be overriden by inherited classes"""
        return ''

    @property
    def _object_type(self) -> str:
        """Returns GNS3 object type, e.g. Project, Template, ..."""
        return self.__class__.__name__

    @property
    def object_id_field_name(self) -> str:
        """Returns GNS3 identifier field name, e.g. project_id, template_id, ..."""
        return self._object_type.lower() + '_id'

    @staticmethod
    def _check_status_code(response: requests_cache.Response):
        """Check HTTP status code received from server"""
        if 200 <= response.status_code < 300:
            return
        raise InvalidParameters(response.text)

    def _get_all(self) -> list:
        """Get all GNS3 objects from server"""
        return self.server.get(url=self._endpoint_url).json()

    def _get(self, objects=None) -> dict:
        """Get all GNS3 objects from server and returns the specified one"""
        if not objects:
            objects = [self.__class__(**t).metadata.dict(include_ro=True) for t in self._get_all()]
        return self.find(objects)

    def find(self, objects):
        object_id = self.metadata.__getattribute__(self.object_id_field_name)
        if object_id:
            try:
                return next(t for t in objects if t[self.object_id_field_name] == object_id)
            except StopIteration:
                raise ObjectDoesNotExist(f'Cannot find {self._object_type} with id "{object_id}" on server')

        name = self.metadata.name
        if name:
            try:
                return next(t for t in objects if 'name' in t and t["name"] == name)
            except StopIteration:
                raise ObjectDoesNotExist(f'Cannot find {self._object_type} with name "{name}" on server')

        _msg: str = f"{self._object_type} metadata must provide either a name or a {self.object_id_field_name}"
        raise InvalidParameters(_msg)

    @property
    def id(self):
        """Returns the GNS3 object identifier, by id first, then by name"""
        endpoint_id = self.metadata.__getattribute__(self.object_id_field_name)
        if endpoint_id:
            return endpoint_id
        response = self._get()
        return response[self.object_id_field_name]

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return Server()

    def read(self) -> None:
        """Get the GNS3 object on server and update the instance, e.g. sync from server"""
        endpoint = self._get()
        self.metadata.update(endpoint)

    def create(self) -> None:
        """Create the GNS3 object on server from the instance, e.g. sync to server"""
        logger.info(f'Creating {self._object_type} {self.metadata.name} ...')
        json = self.metadata.dict()
        response = self.server.post(url=self._endpoint_url, json=json)
        self._check_status_code(response)
        self.metadata.update(response.json())
        self.server.cache.clear()

    def update(self) -> None:
        """Update the GNS3 object on server from the instance, e.g. sync to server"""
        logger.info(f'Updating {self._object_type} {self.metadata.name} ...')
        url = f"{self._endpoint_url}/{self.id}"
        json = self.metadata.dict()
        response = self.server.put(url=url, json=json)
        self._check_status_code(response)
        self.metadata.update(response.json())
        self.server.cache.clear()

    def delete(self) -> None:
        """Delete the GNS3 object on server and reset the instance"""
        logger.info(f'Deleting {self._object_type} {self.metadata.name} ...')
        url = f"{self._endpoint_url}/{self.id}"
        response = self.server.delete(url=url)
        self._check_status_code(response)
        self.metadata = self._MetadataClass()
        self.server.cache.clear()

    @property
    def exists(self, objects=None):
        """Find the object on server and returns if it exists or not"""
        try:
            self._get(objects)
        except ObjectDoesNotExist:
            return False
        return True

    def diff(self, remote_object=None) -> dict:
        """Find the object on server (remote_object) and returns a diff with local instance (self)"""
        if not remote_object:
            remote_object = self._get()
        return self.metadata.diff(remote_object)


class Template(BaseObject):
    _MetadataClass = TemplateMetadata

    def __init__(self, server: Server = None, **kwargs) -> None:
        super(Template, self).__init__(**kwargs)
        self._server = server
        self.metadata = self._MetadataClass(**kwargs)

    @property
    def _endpoint_url(self) -> str:
        return '/templates'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._server

    def create(self) -> None:
        if self.metadata.template_type not in ['nat', 'cloud']:
            super(Template, self).create()


class Project(BaseObject):
    _MetadataClass = ProjectMetadata

    def __init__(self, server: Server = None, **kwargs) -> None:
        super(Project, self).__init__(**kwargs)
        self._server = server
        self.drawings = DrawingList(project=self)
        self.nodes = NodeList(project=self)
        self.links = LinkList(project=self)

    @property
    def _endpoint_url(self) -> str:
        return '/projects'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._server


class Drawing(BaseObject):
    _MetadataClass = DrawingMetadata

    def __init__(self, project: Project = None, **kwargs) -> None:
        super(Drawing, self).__init__(**kwargs)
        self.metadata.update({})
        self.project = project

    @property
    def _endpoint_url(self) -> str:
        return f'/projects/{self.project.id}/drawings'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self.project.server


class Node(BaseObject):
    _MetadataClass = NodeMetadata

    def __init__(self, project: Project = None, template: Template = None, **kwargs) -> None:
        super(Node, self).__init__(**kwargs)
        self.project = project
        self.template = template

    @property
    def _endpoint_url(self) -> str:
        return f'/projects/{self.project.id}/nodes'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self.project.server

    def create(self) -> None:
        """Create the GNS3 object on server from the instance, e.g. sync to server"""
        logger.info(f'Creating {self._object_type} {self.metadata.name} ...')
        if self.template:
            url = f"{self._endpoint_url}/{self.template.id}".replace('/nodes/', '/templates/')
        else:
            url = f"{self._endpoint_url}"
        json = {k: v for k, v in self.metadata.dict().items() if k in ('name', 'compute_id', 'x', 'y')}
        response = self.server.post(url=url, json=json)
        self._check_status_code(response)
        json = self.metadata.dict()
        self.metadata.update(response.json())
        self.server.cache.clear()
        # GNS3 server does not succeed at once, bug ?
        self.metadata.update(json)
        self.update()


class Link(BaseObject):
    _MetadataClass = LinkMetadata

    def __init__(self, project: Project = None, **kwargs) -> None:
        super(Link, self).__init__(**kwargs)
        self.metadata._project = project
        self.metadata.update({})
        self.project = project

    @property
    def _endpoint_url(self) -> str:
        return f'/projects/{self.project.id}/links'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self.project.server

    @staticmethod
    def are_link_ends_the_same(v1, v2) -> bool:
        # syntax checks
        if len(v1) != len(v2) != 2:
            return False
        for n in v1 + v2:
            if 'node' not in n or 'adapter_number' not in n or 'port_number' not in n:
                return False
            if not isinstance(n['node'], Node):
                return False

        # ends definition with node object
        v1p0 = v1[0]['adapter_number'], v1[0]['port_number']
        v1p1 = v1[1]['adapter_number'], v1[1]['port_number']
        v2p0 = v2[0]['adapter_number'], v2[0]['port_number']
        v2p1 = v2[1]['adapter_number'], v2[1]['port_number']
        if (v1p0 + v1p1 == v2p0 + v2p1 and v1[0]['node'] is v2[0]['node'] and v1[1]['node'] is v2[1]['node']) or \
                (v1p0 + v1p1 == v2p1 + v2p0 and v1[0]['node'] is v2[1]['node'] and v1[1]['node'] is v2[0]['node']):
            return True

        # ends definition with node id
        v1p0 = v1[0]['node'].metadata.node_id, v1[0]['adapter_number'], v1[0]['port_number']
        v1p1 = v1[1]['node'].metadata.node_id, v1[1]['adapter_number'], v1[1]['port_number']
        v2p0 = v2[0]['node'].metadata.node_id, v2[0]['adapter_number'], v2[0]['port_number']
        v2p1 = v2[1]['node'].metadata.node_id, v2[1]['adapter_number'], v2[1]['port_number']
        if v1p0 + v1p1 == v2p0 + v2p1 or v1p1 + v1p0 == v2p0 + v2p1:
            if isinstance(v1[0]['node'].metadata.node_id, str) and isinstance(v1[1]['node'].metadata.node_id, str):
                return True

        # ends definition with node name
        v1p0 = v1[0]['node'].metadata.name, v1[0]['adapter_number'], v1[0]['port_number']
        v1p1 = v1[1]['node'].metadata.name, v1[1]['adapter_number'], v1[1]['port_number']
        v2p0 = v2[0]['node'].metadata.name, v2[0]['adapter_number'], v2[0]['port_number']
        v2p1 = v2[1]['node'].metadata.name, v2[1]['adapter_number'], v2[1]['port_number']
        if v1p0 + v1p1 == v2p0 + v2p1 or v1p1 + v1p0 == v2p0 + v2p1:
            if isinstance(v1[0]['node'].metadata.name, str) and isinstance(v1[1]['node'].metadata.name, str):
                return True

        # ends definition with node name and id
        v1p0 = v1[0]['adapter_number'], v1[0]['port_number']
        v1p1 = v1[1]['adapter_number'], v1[1]['port_number']
        v2p0 = v2[0]['adapter_number'], v2[0]['port_number']
        v2p1 = v2[1]['adapter_number'], v2[1]['port_number']
        if (v1p0 + v1p1 == v2p0 + v2p1 and
            (v1[0]['node'].metadata.name and v1[0]['node'].metadata.name == v2[0]['node'].metadata.name
             and v1[1]['node'].metadata.node_id and v1[1]['node'].metadata.node_id == v2[1]['node'].metadata.node_id
             or v1[0]['node'].metadata.node_id and v1[0]['node'].metadata.node_id == v2[0]['node'].metadata.node_id
             and v1[1]['node'].metadata.name and v1[1]['node'].metadata.name == v2[1]['node'].metadata.name)) \
                or (v1p0 + v1p1 == v2p1 + v2p0 and
                    (v1[0]['node'].metadata.name and v1[0]['node'].metadata.name == v2[1]['node'].metadata.name
                     and isinstance(v1[1]['node'].metadata.node_id, str)
                     and v1[1]['node'].metadata.node_id == v2[0]['node'].metadata.node_id
                     or isinstance(v1[0]['node'].metadata.node_id, str)
                     and v1[0]['node'].metadata.node_id == v2[1]['node'].metadata.node_id
                     and v1[1]['node'].metadata.name and v1[1]['node'].metadata.name == v2[0]['node'].metadata.name)):
            return True

        return False

    def _get(self, objects=None):
        """Get all GNS3 objects from server and returns the specified one"""
        if not objects:
            objects = [self.__class__(project=self.project, **t).metadata.dict(include_ro=True)
                       for t in self._get_all()]
        return self.find(objects)

    def find(self, objects):

        object_id = self.metadata.__getattribute__(self.object_id_field_name)
        if object_id:
            try:
                return next(t for t in objects if t[self.object_id_field_name] == object_id)
            except StopIteration:
                raise ObjectDoesNotExist(f'Cannot find {self._object_type} with id "{object_id}" on server')

        nodes = self.metadata.nodes  # noqa
        if nodes:
            try:
                return next(t for t in objects if Link.are_link_ends_the_same(t['nodes'], nodes))
            except StopIteration:
                raise ObjectDoesNotExist(f'Cannot find {self._object_type} with same ends on server')

        _msg: str = f"{self._object_type} metadata must provide either nodes or a {self.object_id_field_name}"
        raise InvalidParameters(_msg)


class BaseObjectList(UserList):
    _ObjectClass = BaseObject

    def __init__(self, initlist=None) -> None:
        super(BaseObjectList, self).__init__(initlist)

    @property
    def _endpoint_url(self) -> str:
        """Property to be overriden by inherited classes"""
        return ''

    def _get(self) -> list:
        """Pull objects from GNS3 server and return them as JSON"""
        return self.server.get(url=self._endpoint_url).json()

    def _get_remote_objects(self) -> list[BaseObject]:
        """Pull objects from GNS3 server and return them as objects"""
        return [self._ObjectClass(**t) for t in self._get()]

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return Server()

    def pull(self) -> None:
        """Pull objects from server and update local instances, e.g. sync from GNS3 server"""
        logger.info(f'Pulling {self.__class__.__name__} ...')
        self.data = self._get_remote_objects()

    def push(self):
        """Push objects to server from local instances, e.g. sync to GNS3 server"""
        logger.info(f'Pushing {self.__class__.__name__} ...')
        diff = self.diff()
        for t in diff['delete']:
            t.delete()
        for t in diff['create']:
            t.create()
        for t in diff['update']:
            t.update()
        self.pull()

    def diff(self) -> dict:
        """Returns the diff between GNS3 server (remote_objects) and local instances (local_objects)"""
        logger.info(f'Diffing {self.__class__.__name__} ...')

        try:
            remote_objects: list[BaseObject] = self._get_remote_objects()
        except ObjectDoesNotExist:
            remote_objects = list()
        remote_objects_ids = set([t.id for t in remote_objects])
        remote_objects_metadatas = {s.id: s.metadata.dict(include_ro=True) for s in remote_objects}

        local_objects: list[BaseObject] = self.data
        local_objects_with_ids = list()
        local_objects_without_ids = list()

        for t in local_objects:
            try:
                s = t.find(remote_objects_metadatas.values())
                t.metadata.update({t.object_id_field_name: s[t.object_id_field_name]})
                local_objects_with_ids.append(t)
            except ObjectDoesNotExist:
                local_objects_without_ids.append(t)

        local_objects_ids = set([t.id for t in local_objects_with_ids])

        delete_ids = remote_objects_ids - local_objects_ids
        update_ids = remote_objects_ids & local_objects_ids

        create_list = local_objects_without_ids
        delete_list = [t for t in remote_objects if t.id in delete_ids]
        update_list = [t for t in local_objects_with_ids
                       if t.id in update_ids and t.diff(remote_objects_metadatas[t.id])]

        return {
            'create': create_list,
            'update': update_list,
            'delete': delete_list
        }


class TemplateList(BaseObjectList):
    _ObjectClass = Template
    _IGNORED_TEMPLATE_TYPES = ('cloud', 'nat', 'frame_relay_switch', 'atm_switch')

    def __init__(self, server: Server, **kwargs) -> None:
        super(TemplateList, self).__init__(**kwargs)
        self._server = server

    @property
    def _endpoint_url(self) -> str:
        return '/templates'

    def diff(self) -> dict:
        """Returns the diff between GNS3 server (remote_objects) and local instances (local_objects)"""
        result = super(TemplateList, self).diff()
        for k in result.keys():
            result[k] = [t for t in result[k] if t.metadata.builtin is not True
                         and t.metadata.template_type not in self._IGNORED_TEMPLATE_TYPES]
        return result

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._server

    def _get_remote_objects(self) -> list[Template]:
        """Pull objects from GNS3 server and return them as objects"""
        return [self._ObjectClass(server=self._server, **t) for t in self._get()]


class ProjectList(BaseObjectList):
    _ObjectClass = Project

    def __init__(self, server: Server, **kwargs) -> None:
        super(ProjectList, self).__init__(**kwargs)
        self._server = server

    @property
    def _endpoint_url(self) -> str:
        return '/projects'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._server

    def _get_remote_objects(self) -> list[Project]:
        """Pull objects from GNS3 server and return them as objects"""
        return [self._ObjectClass(server=self._server, **t) for t in self._get()]


class DrawingList(BaseObjectList):
    _ObjectClass = Drawing

    def __init__(self, project: Project, **kwargs) -> None:
        super(DrawingList, self).__init__(**kwargs)
        self._project = project

    @property
    def _endpoint_url(self) -> str:
        return f'/projects/{self._project.id}/drawings'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._project.server

    def _get_remote_objects(self) -> list[Drawing]:
        """Pull objects from GNS3 server and return them as objects"""
        return [self._ObjectClass(project=self._project, **t) for t in self._get()]


class NodeList(BaseObjectList):
    _ObjectClass = Node

    def __init__(self, project: Project, **kwargs) -> None:
        super(NodeList, self).__init__(**kwargs)
        self._project = project

    @property
    def _endpoint_url(self) -> str:
        return f'/projects/{self._project.id}/nodes'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._project.server

    def _get_remote_objects(self) -> list[Node]:
        """Pull objects from GNS3 server and return them as objects"""
        return [self._ObjectClass(project=self._project, **t) for t in self._get()]


class LinkList(BaseObjectList):
    _ObjectClass = Link

    def __init__(self, project: Project, **kwargs) -> None:
        super(LinkList, self).__init__(**kwargs)
        self._project = project

    @property
    def _endpoint_url(self) -> str:
        return f'/projects/{self._project.id}/links'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._project.server

    def _get_remote_objects(self) -> list[Link]:
        """Pull objects from GNS3 server and return them as objects"""
        return [self._ObjectClass(project=self._project, **t) for t in self._get()]
