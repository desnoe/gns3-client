import requests
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


class Server(requests.Session):
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
        return super(Server, self).request(method, url, *args, **kwargs)

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

    def diff(self, source: dict) -> dict:
        """Returns a dict diff between source and instance (target)"""
        result = dict()
        source_params = {k: v for k, v in source.items() if v is not None}
        target_params = {
            k: v
            for k, v in vars(self).items()
            if v is not None
        }
        for k, v in target_params.items():
            if k not in source_params or k in source_params and source_params[k] != target_params[k]:
                result[k] = target_params[k]

        return result


@dataclass
class TemplateMetadata(BaseObjectMetadata):
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
    console_type: Optional[str] = None
    cpu_throttling: Optional[int] = None
    cpus: Optional[int] = None
    create_config_disk: Optional[bool] = None
    custom_adapters: Optional[list] = None
    default_name_format: Optional[str] = None
    first_port_name: Optional[str] = None
    hda_disk_image: Optional[str] = None
    hda_disk_interface: Optional[str] = None
    hdb_disk_image: Optional[str] = None
    hdb_disk_interface: Optional[str] = None
    hdc_disk_image: Optional[str] = None
    hdc_disk_interface: Optional[str] = None
    hdd_disk_image: Optional[str] = None
    hdd_disk_interface: Optional[str] = None
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
    process_priority: Optional[str] = None
    qemu_path: Optional[str] = None
    ram: Optional[int] = None
    replicate_network_connection_state: Optional[bool] = None
    symbol: Optional[str] = None
    usage: Optional[str] = None


@dataclass
class ProjectMetadata(BaseObjectMetadata):
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
        self._export_svg_field()
        return super(DrawingMetadata, self).dict(include_ro)


@dataclass
class NodeMetadata(BaseObjectMetadata):
    _READONLY_ATTRIBUTES = 'command_line', 'console', 'console_host', 'height', 'node_directory', 'node_id', 'ports',\
                           'project_id', 'status', 'template_id', 'width'

    node_id: Optional[str] = None
    node_type: Optional[str] = None

    command_line: Optional[str] = None
    compute_id: Optional[str] = None
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
    _READONLY_ATTRIBUTES = 'capture_compute_id', 'capture_file_name', 'capture_file_path', 'capturing', 'link_id',\
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
        for node in self.nodes:
            if 'node_id' in node:
                node['node'] = Node(project=self._project, node_id=node['node_id'])
                del node['node_id']

    def _export_nodes_field(self) -> None:
        for node in self.nodes:
            if 'node' in node:
                node['node_id'] = node['node'].id
                del node['node']

    def update(self, data_dict: dict):
        super(LinkMetadata, self).update(data_dict)
        self._import_nodes_field()
        return self

    def dict(self, include_ro: bool = False) -> dict:
        self._export_nodes_field()
        return super(LinkMetadata, self).dict(include_ro)


class BaseObject:
    _MetadataClass = BaseObjectMetadata

    def __init__(self, **kwargs) -> None:
        self.metadata = self._MetadataClass(**kwargs)

    def __repr__(self):
        return self.metadata.__repr__()

    @property
    def _endpoint_url(self) -> str:
        """Property to be overriden by inherited classes"""
        return ''

    @property
    def _object_type(self) -> str:
        """Returns GNS3 object type, e.g. Project, Template, ..."""
        return self.__class__.__name__

    @property
    def _object_id_field_name(self) -> str:
        """Returns GNS3 identifier field name, e.g. project_id, template_id, ..."""
        return self._object_type.lower() + '_id'

    @staticmethod
    def _check_status_code(response: requests.Response):
        """Check HTTP status code received from server"""
        if 200 <= response.status_code < 300:
            return
        raise InvalidParameters(response.text)

    def _get_all(self) -> list:
        """Get all GNS3 objects from server"""
        return self.server.get(url=self._endpoint_url).json()

    def _get(self, object_id: str = None, name: str = None) -> dict:
        """Get all GNS3 objects from server and returns the specified one"""
        objects = [self.__class__(**t).metadata.dict(include_ro=True) for t in self._get_all()]

        if not object_id:
            object_id = self.metadata.__getattribute__(self._object_id_field_name)
        if object_id:
            try:
                return next(t for t in objects if t[self._object_id_field_name] == object_id)
            except StopIteration:
                raise ObjectDoesNotExist(f'Cannot find {self._object_type} with id "{object_id}" on server')

        if not name:
            name = self.metadata.name
        if name:
            try:
                return next(t for t in objects if t["name"] == name)
            except StopIteration:
                raise ObjectDoesNotExist(f'Cannot find {self._object_type} with name "{name}" on server')

        _msg: str = f"{self._object_type} metadata must provide either a name or a {self._object_id_field_name}"
        raise InvalidParameters(_msg)

    @property
    def id(self):
        """Returns the GNS3 object identifier, by id first, then by name"""
        endpoint_id = self.metadata.__getattribute__(self._object_id_field_name)
        if endpoint_id:
            return endpoint_id
        response = self._get()
        return response[self._object_id_field_name]

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
        json = self.metadata.dict()
        response = self.server.post(url=self._endpoint_url, json=json)
        self._check_status_code(response)
        self.metadata.update(response.json())

    def update(self) -> None:
        """Update the GNS3 object on server from the instance, e.g. sync to server"""
        url = f"{self._endpoint_url}/{self.id}"
        json = self.metadata.dict()
        response = self.server.put(url=url, json=json)
        self._check_status_code(response)
        self.metadata.update(response.json())

    def delete(self) -> None:
        """Delete the GNS3 object on server and reset the instance"""
        url = f"{self._endpoint_url}/{self.id}"
        response = self.server.delete(url=url)
        self._check_status_code(response)
        self.metadata = self._MetadataClass()

    @property
    def exists(self):
        """Find the object on server and returns if it exists or not"""
        try:
            self._get()
        except ObjectDoesNotExist:
            return False
        return True

    def diff(self) -> dict:
        """Find the object on server (source) and returns a diff with local instance (target)"""
        source = self._get()
        return self.metadata.diff(source)


class Template(BaseObject):
    _MetadataClass = TemplateMetadata

    def __init__(self, server: Server = None, **kwargs) -> None:
        super(Template, self).__init__(**kwargs)
        self._server = server

    @property
    def _endpoint_url(self) -> str:
        return '/templates'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._server


class Project(BaseObject):
    _MetadataClass = ProjectMetadata

    def __init__(self, server: Server = None, **kwargs) -> None:
        super(Project, self).__init__(**kwargs)
        self._server = server
        self.drawings = DrawingList(project=self)
        self.nodes = NodeList(project=self)

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
        self._project = project

    @property
    def _endpoint_url(self) -> str:
        return f'/projects/{self._project.id}/drawings'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._project.server


class Node(BaseObject):
    _MetadataClass = NodeMetadata

    def __init__(self, project: Project = None, template: Template = None, **kwargs) -> None:
        super(Node, self).__init__(**kwargs)
        self._project = project
        self._template = template

    @property
    def _endpoint_url(self) -> str:
        return f'/projects/{self._project.id}/nodes'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._project.server

    def create(self) -> None:
        """Create the GNS3 object on server from the instance, e.g. sync to server"""
        if self._template:
            url = f"{self._endpoint_url}/{self._template.id}".replace('/nodes/', '/templates/')
        else:
            url = f"{self._endpoint_url}"
        json = self.metadata.dict()
        cache = json.copy()
        response = self.server.post(url=url, json=json)
        self._check_status_code(response)
        self.metadata.update(response.json())
        # GNS3 server does not succeed at once, bug ?
        self.metadata.update(cache)
        self.update()


class Link(BaseObject):
    _MetadataClass = LinkMetadata

    def __init__(self, project: Project = None, **kwargs) -> None:
        super(Link, self).__init__(**kwargs)
        self.metadata._project = project
        self.metadata.update({})
        self._project = project

    @property
    def _endpoint_url(self) -> str:
        return f'/projects/{self._project.id}/links'

    @property
    def server(self):
        """Returns the GNS3 server used by this object"""
        return self._project.server


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
        self.data = self._get_remote_objects()

    def push(self):
        """Push objects to server from local instances, e.g. sync to GNS3 server"""
        diff = self.diff()
        for t in diff['delete']:
            t.delete()
        for t in diff['create']:
            t.create()
        for t in diff['update']:
            t.update()
        self.pull()

    def diff(self) -> dict:
        """Returns the diff between GNS3 server (source) and local instances (target)"""
        target: list[BaseObject] = self.data
        target_with_ids = [t for t in target if t.exists]
        target_without_ids = [t for t in target if t not in target_with_ids]
        target_ids = set([t.id for t in target_with_ids])

        source: list[BaseObject] = self._get_remote_objects()
        source_ids = set([t.id for t in source])

        delete_ids = source_ids - target_ids
        update_ids = source_ids & target_ids

        create_list = target_without_ids
        delete_list = [t for t in source if t.id in delete_ids]
        update_list = [t for t in target_with_ids if t.id in update_ids and t.diff()]

        return {
            'create': create_list,
            'update': update_list,
            'delete': delete_list
        }


class TemplateList(BaseObjectList):
    _ObjectClass = Template
    _IGNORED_TEMPLATE_TYPES = ('nat', 'frame_relay_switch', 'atm_switch')

    def __init__(self, server: Server, **kwargs) -> None:
        super(TemplateList, self).__init__(**kwargs)
        self._server = server

    @property
    def _endpoint_url(self) -> str:
        return '/templates'

    def _get(self) -> list:
        return [t for t in super(TemplateList, self)._get()
                if t['template_type'] not in self._IGNORED_TEMPLATE_TYPES]

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
