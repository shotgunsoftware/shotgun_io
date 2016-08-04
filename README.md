# shotgun_io
Provides interaction with Shotgun specific for render queue integrations. `shotgun_io` supports a simple command line interface.

### Overview
The purpose of `shotgun_io` is to provide a simplified wrapper around the Shotgun API to facilitate integrating render queues with Shotgun. By removing the Shotgun-specific code from the render queue itself, it requires less effort for vendors to add support for the integration, and makes it easy for studios to configure and update the integration piece independently of their render queue system. `shotgun_io` is the “go-between” sitting in the middle of your Shotgun instance and your render queue system.

`shotgun_io` enables studios to customize the way the integration functions to match their specific workflow through configuration options or more advanced method overrides.

### Documentation
Documentation is available at http://developer.shotgunsoftware.com/shotgun_io

### Supported Render Queues
The `shotgun_io` module is currently supported by [Rush](http://seriss.com/rush/).
