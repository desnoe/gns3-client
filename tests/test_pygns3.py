import unittest
import logzero
from pygns3 import Server, Template, TemplateList, Project, ProjectList, Drawing, DrawingList, \
    DrawingMetadata, Node, NodeList, Link, LinkList

GNS3_URL = 'http://172.25.41.100:3080/v2'

logzero.loglevel(level=20)


class TestServer(unittest.TestCase):
    def setUp(self):
        self.server = Server(GNS3_URL)

    def tearDown(self):
        self.server.close()

    def test_version(self):
        version = self.server.version()
        self.assertIn('version', version)


class TestTemplate(unittest.TestCase):
    def setUp(self):
        self.server = Server(GNS3_URL)
        template = Template(name='test_template', template_type="qemu", server=self.server)
        while template.exists:
            template.delete()
            template = Template(name='test_template', template_type="qemu", server=self.server)

    def tearDown(self):
        template = Template(name='test_template', template_type="qemu", server=self.server)
        while template.exists:
            template.delete()
            template = Template(name='test_template', template_type="qemu", server=self.server)
        self.server.close()

    def test_get_id(self):
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.create()
        template_id = template.id
        self.assertIsInstance(template_id, str)
        self.assertGreater(len(template_id), 0)

    def test_create(self):
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.create()
        self.assertIsNotNone(template.metadata.template_id)

    def test_read(self):
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.create()
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.read()
        self.assertIsNotNone(template.metadata.template_id)

    def test_update(self):
        template = Template(name='test_template', template_type="qemu", console_type="telnet", server=self.server)
        template.create()
        template = Template(name='test_template', template_type="qemu", console_type="vnc", server=self.server)
        template.update()
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.read()
        self.assertEqual(template.metadata.console_type, 'vnc')

    def test_delete(self):
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.create()
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.delete()
        self.assertIsNone(template.metadata.template_id)

    def test_exists(self):
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.create()
        self.assertTrue(template.exists)
        template = Template(name='test_template', template_type="qemu", server=self.server)
        self.assertTrue(template.exists)
        template = Template(name='test_no_template', template_type="qemu", server=self.server)
        self.assertFalse(template.exists)


class TestTemplates(unittest.TestCase):
    def setUp(self):
        self.server = Server(GNS3_URL)
        template = Template(name='test_template', template_type="qemu", server=self.server)
        while template.exists:
            template.delete()
            template = Template(name='test_template', template_type="qemu", server=self.server)

    def tearDown(self):
        template = Template(name='test_template', template_type="qemu", server=self.server)
        while template.exists:
            template.delete()
            template = Template(name='test_template', template_type="qemu", server=self.server)
        self.server.close()

    def test_pull(self):
        self.server.templates.pull()
        self.assertGreater(len(self.server.templates), 0)

    def test_diff_add(self):
        self.server.templates.pull()
        self.server.templates.append(Template(name='test_template', template_type="qemu", server=self.server))
        diff = self.server.templates.diff()
        self.assertEqual((1, 0, 0), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_diff_delete(self):
        self.server.templates.pull()
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.create()
        diff = self.server.templates.diff()
        self.assertEqual((0, 0, 1), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_diff_update(self):
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.create()
        self.server.templates.pull()
        template.metadata.console_type = 'vnc'
        template.update()
        diff = self.server.templates.diff()
        self.assertEqual((0, 1, 0), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_push_add(self):
        self.server.templates.pull()
        nb_templates_before = len(self.server.templates)
        self.server.templates.append(Template(name='test_template', template_type="qemu", server=self.server))
        self.server.templates.push()
        nb_templates_after = len(self.server.templates)
        self.assertEqual(nb_templates_after, nb_templates_before + 1)

    def test_push_delete(self):
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.create()
        self.server.templates.pull()
        nb_templates_before = len(self.server.templates)
        templates = [t for t in self.server.templates if t.metadata.name != 'test_template']
        self.server.templates = TemplateList(server=self.server, initlist=templates)
        self.server.templates.push()
        nb_templates_after = len(self.server.templates)
        self.assertEqual(nb_templates_after, nb_templates_before - 1)

    def test_push_update(self):
        template = Template(name='test_template', template_type="qemu", server=self.server)
        template.create()
        self.server.templates.pull()
        template = next(t for t in self.server.templates if t.metadata.name == 'test_template')
        self.assertEqual(template.metadata.console_type, 'telnet')
        template.metadata.console_type = 'vnc'
        self.server.templates.push()
        template = next(t for t in self.server.templates if t.metadata.name == 'test_template')
        self.assertEqual(template.metadata.console_type, 'vnc')


class TestProject(unittest.TestCase):
    def setUp(self):
        self.server = Server(GNS3_URL)
        project = Project(name='test_project', server=self.server)
        if project.exists:
            project.delete()

    def tearDown(self):
        project = Project(name='test_project', server=self.server)
        if project.exists:
            project.delete()
        self.server.close()

    def test_get_id(self):
        project = Project(name='test_project', server=self.server)
        project.create()
        project_id = project.id
        self.assertIsInstance(project_id, str)
        self.assertGreater(len(project_id), 0)

    def test_create(self):
        project = Project(name='test_project', server=self.server)
        project.create()
        self.assertIsNotNone(project.metadata.project_id)

    def test_read(self):
        project = Project(name='test_project', server=self.server)
        project.create()
        project = Project(name='test_project', server=self.server)
        project.read()
        self.assertIsNotNone(project.metadata.project_id)

    def test_update(self):
        project = Project(name='test_project', auto_close=False, server=self.server)
        project.create()
        project.metadata.auto_close = True
        project.update()
        project.read()
        self.assertTrue(project.metadata.auto_close)
        project.metadata.auto_close = False
        project.update()
        project.read()
        self.assertFalse(project.metadata.auto_close)

    def test_delete(self):
        project = Project(name='test_project', server=self.server)
        project.create()
        project = Project(name='test_project', server=self.server)
        project.delete()
        self.assertIsNone(project.metadata.project_id)

    def test_exists(self):
        project = Project(name='test_project', server=self.server)
        project.create()
        self.assertTrue(project.exists)
        project = Project(name='test_project', server=self.server)
        self.assertTrue(project.exists)
        project = Project(name='test_no_project', server=self.server)
        self.assertFalse(project.exists)


class TestProjects(unittest.TestCase):
    def setUp(self):
        self.server = Server(GNS3_URL)
        project = Project(name='test_project', server=self.server)
        if project.exists:
            project.delete()

    def tearDown(self):
        project = Project(name='test_project', server=self.server)
        if project.exists:
            project.delete()
        self.server.close()

    def test_pull(self):
        project = Project(name='test_project', server=self.server)
        project.create()
        self.server.projects.pull()
        self.assertEqual(len(self.server.projects), 1)

    def test_diff_add(self):
        self.server.projects.pull()
        self.server.projects.append(Project(name='test_project', server=self.server))
        diff = self.server.projects.diff()
        self.assertEqual((1, 0, 0), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_diff_delete(self):
        self.server.projects.pull()
        project = Project(name='test_project', server=self.server)
        project.create()
        diff = self.server.projects.diff()
        self.assertEqual((0, 0, 1), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_diff_update(self):
        project = Project(name='test_project', server=self.server, auto_close=False)
        project.create()
        self.server.projects.pull()
        project.metadata.auto_close = True
        project.update()
        diff = self.server.projects.diff()
        self.assertEqual((0, 1, 0), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_push_add(self):
        self.server.projects.pull()
        nb_projects_before = len(self.server.projects)
        self.server.projects.append(Project(name='test_project', server=self.server))
        self.server.projects.push()
        nb_projects_after = len(self.server.projects)
        self.assertEqual(nb_projects_after, nb_projects_before + 1)

    def test_push_delete(self):
        project = Project(name='test_project', server=self.server)
        project.create()
        self.server.projects.pull()
        nb_projects_before = len(self.server.projects)
        projects = [t for t in self.server.projects if t.metadata.name != 'test_project']
        self.server.projects = ProjectList(server=self.server, initlist=projects)
        self.server.projects.push()
        nb_projects_after = len(self.server.projects)
        self.assertEqual(nb_projects_after, nb_projects_before - 1)

    def test_push_update(self):
        project = Project(name='test_project', server=self.server)
        project.create()
        self.server.projects.pull()
        project = next(t for t in self.server.projects if t.metadata.name == 'test_project')
        self.assertEqual(project.metadata.auto_close, True)
        project.metadata.auto_close = False
        self.server.projects.push()
        project = next(t for t in self.server.projects if t.metadata.name == 'test_project')
        self.assertEqual(project.metadata.auto_close, False)


class TestDrawing(unittest.TestCase):
    SVG_WITH_NAME = '<svg height="{0}" width="{1}" name="test_drawing">' \
                    '<rect fill="#ebecff" fill-opacity="1.0" height="{0}" width="{1}" />' \
                    '</svg>'.format(100, 100)
    SVG_WITHOUT_NAME = '<svg height="{0}" width="{1}">' \
                       '<rect fill="#ebecff" fill-opacity="1.0" height="{0}" width="{1}" />' \
                       '</svg>'.format(100, 100)
    server: Server

    @classmethod
    def setUpClass(cls):
        cls.server = Server(GNS3_URL)
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()

    @classmethod
    def tearDownClass(cls):
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()
        cls.server.close()

    def setUp(self):
        self.project = Project(name='test_project', server=self.server)
        if not self.project.exists:
            self.project.create()
        self.project.read()

    def tearDown(self):
        if self.project.exists:
            self.project.delete()

    def test_get_name_from_svg(self):
        drawing = Drawing(project=self.project, svg=self.SVG_WITH_NAME)
        m: DrawingMetadata = drawing.metadata
        self.assertEqual('test_drawing', m.name)
        self.assertEqual(self.SVG_WITHOUT_NAME, m.svg)

    def test_set_name_from_svg(self):
        drawing = Drawing(project=self.project, svg=self.SVG_WITHOUT_NAME)
        m: DrawingMetadata = drawing.metadata
        m.name = 'test_drawing'
        svg = m.dict()['svg']
        self.assertEqual(self.SVG_WITH_NAME, svg)

    def test_get_id(self):
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        drawing_id = drawing.id
        self.assertIsInstance(drawing_id, str)
        self.assertGreater(len(drawing_id), 0)

    def test_create(self):
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        self.assertIsNotNone(drawing.id)
        self.assertEqual('test_drawing', drawing.metadata.name)

    def test_read(self):
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.read()
        self.assertIsNotNone(drawing.metadata.drawing_id)

    def test_update(self):
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        drawing.metadata.x = 100
        drawing.update()
        drawing.read()
        self.assertEqual(drawing.metadata.x, 100)
        drawing.metadata.x = 200
        drawing.update()
        drawing.read()
        self.assertEqual(drawing.metadata.x, 200)

    def test_delete(self):
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.delete()
        self.assertIsNone(drawing.metadata.drawing_id)

    def test_exists(self):
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        self.assertTrue(drawing.exists)
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        self.assertTrue(drawing.exists)
        drawing = Drawing(name='test_no_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        self.assertFalse(drawing.exists)


class TestDrawings(unittest.TestCase):
    SVG_WITH_NAME = '<svg height="{0}" width="{1}" name="test_drawing">' \
                    '<rect fill="#ebecff" fill-opacity="1.0" height="{0}" width="{1}" />' \
                    '</svg>'.format(100, 100)
    SVG_WITHOUT_NAME = '<svg height="{0}" width="{1}">' \
                       '<rect fill="#ebecff" fill-opacity="1.0" height="{0}" width="{1}" />' \
                       '</svg>'.format(100, 100)
    server: Server

    @classmethod
    def setUpClass(cls):
        cls.server = Server(GNS3_URL)
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()

    @classmethod
    def tearDownClass(cls):
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()
        cls.server.close()

    def setUp(self):
        self.project = Project(name='test_project', server=self.server)
        if not self.project.exists:
            self.project.create()
        self.project.read()

    def tearDown(self):
        if self.project.exists:
            self.project.delete()

    def test_pull(self):
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        self.project.drawings.pull()
        self.assertEqual(len(self.project.drawings), 1)

    def test_diff_add(self):
        self.project.drawings.pull()
        self.project.drawings.append(Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME))
        diff = self.project.drawings.diff()
        self.assertEqual((1, 0, 0), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_diff_delete(self):
        self.project.drawings.pull()
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        diff = self.project.drawings.diff()
        self.assertEqual((0, 0, 1), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_diff_update(self):
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        self.project.drawings.pull()
        drawing.metadata.svg = self.SVG_WITHOUT_NAME.replace('100', '200')
        drawing.update()
        diff = self.project.drawings.diff()
        self.assertEqual((0, 1, 0), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_push_add(self):
        self.project.drawings.pull()
        nb_drawings_before = len(self.project.drawings)
        self.project.drawings.append(Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME))
        self.project.drawings.push()
        nb_drawings_after = len(self.project.drawings)
        self.assertEqual(nb_drawings_after, nb_drawings_before + 1)

    def test_push_delete(self):
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        self.project.drawings.pull()
        nb_drawings_before = len(self.project.drawings)
        drawings = [t for t in self.project.drawings if t.metadata.name != 'test_drawing']
        self.project.drawings = DrawingList(project=self.project, initlist=drawings)
        self.project.drawings.push()
        nb_drawings_after = len(self.project.drawings)
        self.assertEqual(nb_drawings_after, nb_drawings_before - 1)

    def test_push_update(self):
        drawing = Drawing(name='test_drawing', project=self.project, svg=self.SVG_WITHOUT_NAME)
        drawing.create()
        self.project.drawings.pull()
        drawing = next(t for t in self.project.drawings if t.metadata.name == 'test_drawing')
        self.assertEqual(drawing.metadata.svg, self.SVG_WITHOUT_NAME)
        drawing.metadata.svg = self.SVG_WITHOUT_NAME.replace('100', '200')
        self.project.drawings.push()
        drawing = next(t for t in self.project.drawings if t.metadata.name == 'test_drawing')
        self.assertEqual(drawing.metadata.svg, self.SVG_WITHOUT_NAME.replace('100', '200'))


class TestNode(unittest.TestCase):
    server: Server
    template: Template

    @classmethod
    def setUpClass(cls):
        cls.server = Server(GNS3_URL)
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()

        template = Template(name='test_template', template_type="qemu", server=cls.server)
        while template.exists:
            template.delete()
            template = Template(name='test_template', template_type="qemu", server=cls.server)
        cls.template = Template(name='test_template', template_type="qemu", server=cls.server)
        cls.template.create()

    @classmethod
    def tearDownClass(cls):
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()
        cls.server.close()

    def setUp(self):
        self.project = Project(name='test_project', server=self.server)
        if not self.project.exists:
            self.project.create()
        self.project.read()

    def tearDown(self):
        if self.project.exists:
            self.project.delete()

    def test_get_id(self):
        node = Node(name='test_node', template=self.template, project=self.project)
        node.create()
        node_id = node.id
        self.assertIsInstance(node_id, str)
        self.assertGreater(len(node_id), 0)

    def test_create(self):
        node = Node(name='test_node', template=self.template, project=self.project)
        node.create()
        self.assertIsNotNone(node.metadata.node_id)

    def test_read(self):
        node = Node(name='test_node', template=self.template, project=self.project)
        node.create()
        node = Node(name='test_node', template=self.template, project=self.project)
        node.read()
        self.assertIsNotNone(node.metadata.node_id)

    def test_update(self):
        node = Node(name='test_node', template=self.template, project=self.project)
        node.create()
        node.metadata.x = 100
        node.update()
        node.read()
        self.assertEqual(node.metadata.x, 100)
        node.metadata.x = 200
        node.update()
        node.read()
        self.assertEqual(node.metadata.x, 200)

    def test_delete(self):
        node = Node(name='test_node', template=self.template, project=self.project)
        node.create()
        node = Node(name='test_node', template=self.template, project=self.project)
        node.delete()
        self.assertIsNone(node.metadata.node_id)

    def test_exists(self):
        node = Node(name='test_node', template=self.template, project=self.project)
        node.create()
        self.assertTrue(node.exists)
        node = Node(name='test_node', template=self.template, project=self.project)
        self.assertTrue(node.exists)
        node = Node(name='test_no_node', template=self.template, project=self.project)
        self.assertFalse(node.exists)


class TestNodes(unittest.TestCase):
    server: Server
    template: Template

    @classmethod
    def setUpClass(cls):
        cls.server = Server(GNS3_URL)
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()

        template = Template(name='test_template', template_type="qemu", server=cls.server)
        while template.exists:
            template.delete()
            template = Template(name='test_template', template_type="qemu", server=cls.server)
        cls.template = Template(name='test_template', template_type="qemu", server=cls.server)
        cls.template.create()

    @classmethod
    def tearDownClass(cls):
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()
        cls.server.close()

    def setUp(self):
        self.project = Project(name='test_project', server=self.server)
        if not self.project.exists:
            self.project.create()
        self.project.read()

    def tearDown(self):
        if self.project.exists:
            self.project.delete()

    def test_pull(self):
        node = Node(name='test_node', template=self.template, project=self.project)
        node.create()
        self.project.nodes.pull()
        self.assertEqual(len(self.project.nodes), 1)

    def test_diff_add(self):
        self.project.nodes.pull()
        self.project.nodes.append(Node(name='test_node', template=self.template, project=self.project))
        diff = self.project.nodes.diff()
        self.assertEqual((1, 0, 0), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_diff_delete(self):
        self.project.nodes.pull()
        node = Node(name='test_node', template=self.template, project=self.project)
        node.create()
        diff = self.project.nodes.diff()
        self.assertEqual((0, 0, 1), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_diff_update(self):
        node = Node(name='test_node', template=self.template, project=self.project)
        node.create()
        self.project.nodes.pull()
        node.metadata.x = 200
        node.update()
        diff = self.project.nodes.diff()
        self.assertEqual((0, 1, 0), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_push_add(self):
        self.project.nodes.pull()
        nb_nodes_before = len(self.project.nodes)
        self.project.nodes.append(Node(name='test_node', template=self.template, project=self.project))
        self.project.nodes.push()
        nb_nodes_after = len(self.project.nodes)
        self.assertEqual(nb_nodes_after, nb_nodes_before + 1)

    def test_push_delete(self):
        node = Node(name='test_node', template=self.template, project=self.project)
        node.create()
        self.project.nodes.pull()
        nb_nodes_before = len(self.project.nodes)
        nodes = [t for t in self.project.nodes if t.metadata.name != 'test_node']
        self.project.nodes = NodeList(project=self.project, initlist=nodes)
        self.project.nodes.push()
        nb_nodes_after = len(self.project.nodes)
        self.assertEqual(nb_nodes_after, nb_nodes_before - 1)

    def test_push_update(self):
        node = Node(name='test_node', template=self.template, project=self.project, x=100)
        node.create()
        self.project.nodes.pull()
        node = next(t for t in self.project.nodes if t.metadata.name == 'test_node')
        self.assertEqual(node.metadata.x, 100)
        node.metadata.x = 200
        self.project.nodes.push()
        node = next(t for t in self.project.nodes if t.metadata.name == 'test_node')
        self.assertEqual(node.metadata.x, 200)


class TestLinkEquality(unittest.TestCase):
    def test_are_link_ends_the_same_ok_object(self):
        # check ok based on Node object
        nodes = [
            {'adapter_number': 0, 'node': Node(), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(), 'port_number': 0}
        ]
        self.assertTrue(Link.are_link_ends_the_same(nodes, nodes))
        self.assertTrue(Link.are_link_ends_the_same(nodes, [nodes[1], nodes[0]]))
        self.assertTrue(Link.are_link_ends_the_same([nodes[1], nodes[0]], nodes))

    def test_are_link_ends_the_same_ko_object(self):
        # check ko based on Node object
        nodes = [
            {'adapter_number': 0, 'node': Node(), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(), 'port_number': 0}
        ]
        nodes2 = [
            {'adapter_number': 0, 'node': Node(), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(), 'port_number': 0}
        ]
        self.assertFalse(Link.are_link_ends_the_same(nodes, nodes2))
        self.assertFalse(Link.are_link_ends_the_same(nodes, [nodes2[1], nodes2[0]]))
        self.assertFalse(Link.are_link_ends_the_same([nodes[1], nodes[0]], nodes2))

    def test_are_link_ends_the_same_ok_id(self):
        # check ok based on Node id
        nodes = [
            {'adapter_number': 0, 'node': Node(node_id='1'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(node_id='2'), 'port_number': 0}
        ]
        nodes2 = [
            {'adapter_number': 0, 'node': Node(node_id='1'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(node_id='2'), 'port_number': 0}
        ]
        self.assertTrue(Link.are_link_ends_the_same(nodes, nodes2))
        self.assertTrue(Link.are_link_ends_the_same(nodes, [nodes2[1], nodes2[0]]))
        self.assertTrue(Link.are_link_ends_the_same([nodes[1], nodes[0]], nodes2))

    def test_are_link_ends_the_same_ko_id(self):
        # check ko based on Node id
        nodes = [
            {'adapter_number': 0, 'node': Node(node_id='1'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(node_id='2'), 'port_number': 0}
        ]
        nodes2 = [
            {'adapter_number': 0, 'node': Node(node_id='3'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(node_id='2'), 'port_number': 0}
        ]
        self.assertFalse(Link.are_link_ends_the_same(nodes, nodes2))
        self.assertFalse(Link.are_link_ends_the_same(nodes, [nodes2[1], nodes2[0]]))
        self.assertFalse(Link.are_link_ends_the_same([nodes[1], nodes[0]], nodes2))

    def test_are_link_ends_the_same_ok_name(self):
        # check ok based on Node name
        nodes = [
            {'adapter_number': 0, 'node': Node(name='test_node1'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(name='test_node2'), 'port_number': 0}
        ]
        nodes2 = [
            {'adapter_number': 0, 'node': Node(name='test_node1'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(name='test_node2'), 'port_number': 0}
        ]
        self.assertTrue(Link.are_link_ends_the_same(nodes, nodes2))
        self.assertTrue(Link.are_link_ends_the_same(nodes, [nodes2[1], nodes2[0]]))
        self.assertTrue(Link.are_link_ends_the_same([nodes[1], nodes[0]], nodes2))

    def test_are_link_ends_the_same_ko_name(self):
        # check ko based on Node name
        nodes = [
            {'adapter_number': 0, 'node': Node(name='test_node1'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(name='test_node2'), 'port_number': 0}
        ]
        nodes2 = [
            {'adapter_number': 0, 'node': Node(name='test_node3'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(name='test_node2'), 'port_number': 0}
        ]
        self.assertFalse(Link.are_link_ends_the_same(nodes, nodes2))
        self.assertFalse(Link.are_link_ends_the_same(nodes, [nodes2[1], nodes2[0]]))
        self.assertFalse(Link.are_link_ends_the_same([nodes[1], nodes[0]], nodes2))

    def test_are_link_ends_the_same_ok_cross(self):
        # cross check based on Node name and id
        nodes = [
            {'adapter_number': 0, 'node': Node(node_id='1'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(name='test_node2'), 'port_number': 0}
        ]
        nodes2 = [
            {'adapter_number': 0, 'node': Node(node_id='1'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(name='test_node2'), 'port_number': 0}
        ]
        self.assertTrue(Link.are_link_ends_the_same(nodes, nodes2))
        self.assertTrue(Link.are_link_ends_the_same(nodes, [nodes2[1], nodes2[0]]))
        self.assertTrue(Link.are_link_ends_the_same([nodes[1], nodes[0]], nodes2))

    def test_are_link_ends_the_same_ko_cross(self):
        # cross check based on Node name and id
        nodes = [
            {'adapter_number': 0, 'node': Node(node_id='1'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(name='test_node2'), 'port_number': 0}
        ]
        nodes2 = [
            {'adapter_number': 0, 'node': Node(node_id='3'), 'port_number': 0},
            {'adapter_number': 0, 'node': Node(name='test_node2'), 'port_number': 0}
        ]
        self.assertFalse(Link.are_link_ends_the_same(nodes, nodes2))
        self.assertFalse(Link.are_link_ends_the_same(nodes, [nodes2[1], nodes2[0]]))
        self.assertFalse(Link.are_link_ends_the_same([nodes[1], nodes[0]], nodes2))


class TestLink(unittest.TestCase):
    server: Server
    template: Template

    @classmethod
    def setUpClass(cls):
        cls.server = Server(GNS3_URL)
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()

        template = Template(name='test_template', template_type="qemu", server=cls.server)
        while template.exists:
            template.delete()
            template = Template(name='test_template', template_type="qemu", server=cls.server)
        cls.template = Template(name='test_template', template_type="qemu", server=cls.server)
        cls.template.create()

    @classmethod
    def tearDownClass(cls):
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()
        cls.server.close()

    def setUp(self):
        self.project = Project(name='test_project', server=self.server)
        if not self.project.exists:
            self.project.create()
        self.project.read()

        self.node1 = Node(name='test_node1', template=self.template, project=self.project)
        self.node1.create()

        self.node2 = Node(name='test_node2', template=self.template, project=self.project)
        self.node2.create()

        self.NODES = [
            {'adapter_number': 0, 'node': self.node1, 'port_number': 0},
            {'adapter_number': 0, 'node': self.node2, 'port_number': 0}
        ]

    def tearDown(self):
        if self.project.exists:
            self.project.delete()

    def test_get_id(self):
        link = Link(project=self.project, nodes=self.NODES)
        link.create()
        link_id = link.id
        self.assertIsInstance(link_id, str)
        self.assertGreater(len(link_id), 0)

    def test_create(self):
        link = Link(project=self.project, nodes=self.NODES)
        link.create()
        self.assertIsNotNone(link.metadata.link_id)

    def test_read(self):
        link = Link(project=self.project, nodes=self.NODES)
        link.create()
        link = Link(project=self.project, nodes=self.NODES)
        link.read()
        self.assertIsNotNone(link.metadata.link_id)

    def test_update(self):
        link = Link(project=self.project, nodes=self.NODES)
        link.create()
        link.metadata.suspend = True
        link.update()
        link.read()
        self.assertEqual(link.metadata.suspend, True)
        link.metadata.suspend = False
        link.update()
        link.read()
        self.assertEqual(link.metadata.suspend, False)

    def test_delete(self):
        link = Link(project=self.project, nodes=self.NODES)
        link.create()
        link = Link(project=self.project, nodes=self.NODES)
        link.delete()
        self.assertIsNone(link.metadata.link_id)

    def test_exists(self):
        link = Link(project=self.project, nodes=self.NODES)
        link.create()
        self.assertTrue(link.exists)
        link = Link(project=self.project, nodes=self.NODES)
        self.assertTrue(link.exists)
        self.NODES[0]['adapter_number'] = 1
        link = Link(project=self.project, nodes=self.NODES)
        self.assertFalse(link.exists)


class TestLinks(unittest.TestCase):
    server: Server
    template: Template

    @classmethod
    def setUpClass(cls):
        cls.server = Server(GNS3_URL)
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()

        template = Template(name='test_template', template_type="qemu", server=cls.server)
        while template.exists:
            template.delete()
            template = Template(name='test_template', template_type="qemu", server=cls.server)
        cls.template = Template(name='test_template', template_type="qemu", server=cls.server)
        cls.template.create()

    @classmethod
    def tearDownClass(cls):
        project = Project(name='test_project', server=cls.server)
        if project.exists:
            project.delete()
        cls.server.close()

    def setUp(self):
        self.project = Project(name='test_project', server=self.server)
        if not self.project.exists:
            self.project.create()
        self.project.read()

        self.node1 = Node(name='test_node1', template=self.template, project=self.project)
        self.node1.create()

        self.node2 = Node(name='test_node2', template=self.template, project=self.project)
        self.node2.create()

        self.NODES = [
            {'adapter_number': 0, 'node': self.node1, 'port_number': 0},
            {'adapter_number': 0, 'node': self.node2, 'port_number': 0}
        ]

    def tearDown(self):
        if self.project.exists:
            self.project.delete()

    def test_pull(self):
        link = Link(project=self.project, nodes=self.NODES)
        link.create()
        self.project.links.pull()
        self.assertEqual(len(self.project.links), 1)

    def test_diff_add(self):
        self.project.links.pull()
        self.project.links.append(Link(project=self.project, nodes=self.NODES))
        diff = self.project.links.diff()
        self.assertEqual((1, 0, 0), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_diff_delete(self):
        self.project.links.pull()
        link = Link(project=self.project, nodes=self.NODES)
        link.create()
        diff = self.project.links.diff()
        self.assertEqual((0, 0, 1), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_diff_update(self):
        link = Link(project=self.project, nodes=self.NODES, suspend=True)
        link.create()
        self.project.links.pull()
        link.metadata.suspend = False
        link.update()
        diff = self.project.links.diff()
        self.assertEqual((0, 1, 0), (len(diff['create']), len(diff['update']), len(diff['delete'])))

    def test_push_add(self):
        self.project.links.pull()
        nb_links_before = len(self.project.links)
        self.project.links.append(Link(project=self.project, nodes=self.NODES))
        self.project.links.push()
        nb_links_after = len(self.project.links)
        self.assertEqual(nb_links_after, nb_links_before + 1)

    def test_push_delete(self):
        link = Link(project=self.project, nodes=self.NODES)
        link.create()
        self.project.links.pull()
        nb_links_before = len(self.project.links)
        self.project.links = LinkList(project=self.project, initlist=[])
        self.project.links.push()
        nb_links_after = len(self.project.links)
        self.assertEqual(nb_links_after, nb_links_before - 1)

    def test_push_update(self):
        link = Link(project=self.project, nodes=self.NODES, suspend=True)
        link.create()
        self.project.links.pull()
        link = self.project.links[0]
        self.assertEqual(link.metadata.suspend, True)
        link.metadata.suspend = False
        self.project.links.push()
        link = self.project.links[0]
        self.assertEqual(link.metadata.suspend, False)


if __name__ == '__main__':
    unittest.main()
