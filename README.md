[![Python 3.9](https://img.shields.io/badge/python-3.9-green.svg)](https://docs.python.org/3.9/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

# gns3-client

*gns3-client* is a Python library that can be used to interact with a [GNS3 server](https://github.com/GNS3/gns3-server)
using its HTTP REST API. A GNS3 server manages emulators or hypervisors such as Dynamips, VirtualBox or Qemu/KVM.

## Disclaimer

This library does not aim at explaining nor documenting in any way the GNS3 server API. Please check
the [GNS3 server official documentation](https://gns3-server.readthedocs.io/en/latest/index.html) for further
information.

## Getting Started

Tests provide a very good starting point.

### Prerequisites

You'll need a [GNS3 server](https://github.com/GNS3/gns3-server) appliance or virtual machine to use the library.
Instructions on how to install a server appliance or virtual machine can be found on
the [GNS3 website](https://www.gns3.com/).

### Installing

```
pip install gns3-client
```

## Running the tests

You'll need a [GNS3 server](https://github.com/GNS3/gns3-server) appliance or virtual machine to test the library.
Instructions on how to install a server appliance or virtual machine can be found on
the [GNS3 website](https://www.gns3.com/).

Location of this test server is provided via these 2 environment variables:

| Environment variable name | Description                                 |             Example             |
|:-------------------------:|---------------------------------------------|:-------------------------------:|
|     `GNS3_SERVER_URL`     | The URL of the GNS3 test server             | http://gns3.example.com:3080/v2 |

You then simply need to perform a `python -v tests/`.

## Limitations

In this version, all [CRUD operations](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) of the following
object types have been implemented:

- projects
- templates
- nodes
- links
- drawings

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see
the [tags on this repository](https://github.com/desnoe/gns3-client/tags).

## Authors

* **Olivier Desnoë** - *Initial work* - [Albatross Networks](http://albatross-networks.com)

See also the list of [contributors](https://github.com/desnoe/gns3-client/contributors) who participated in this
project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
