# Using-Runbook-Data-Layer

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866999481/Using-Runbook-Data-Layer

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:19 AM

---

Working with Data Clients in Automations
========================================

This document will cover the Runbook Data Layer (RLD).

What is RDL
-----------

RDL sits between automations and data sources, allowing for the separation of “what” data from “where” the data is stored by creating the concept of Data Client vs Data Provider. This allows consultants to change the “where” of the data without impacting the automations. It is deployed as a Lambda layer, which all automations will use to get data it needs to complete.

We currently rely on CMF as the data provider. Therefore, it is expected that CMF metadata store will be populated with Servers, Applications, and Waves. However, New Data Clients and Data Providers can be created as needed following the below guidance.

How to use the existent data clients
------------------------------------

RDL is used via the data client, all clients extend the BaseClient which has the following methods:
- `get(id: str = None)`
- Use this function to get a single resource or all resources, if id is not defiend, it returns all resources
- `get_filtered(filter_dict: Dict[str, Union[Any, List[Any]]])`
- Use this function to get filtered resources using an `AND` filter compounding
- `create(item:Dict)`
- Use this function to create a new resource, note schema validation is currently not supported by the client.
- `delete(id: str)`
- Use this function to delete a specific resource using the id
- `update(id: str, item: Dict)`
- Use this function to update specific resource using the id

We solely rely on the CMF data provider currently, but new providers can be added as needed.

Currently we have the following data clients availabe to use out of the box:
- WaveClient
- AppClient
- ServerClient
- DatabaseClient

Here is an example of how to use the AppClient

```

First thing we need to do is import the AppClient
=================================================

from aws\_automation\_helpers.runbook\_data\_layer.clients.app\_client import AppClient

next we need to initialize it, an instance of the aws\_lambda\_powertools logger will need to be passed so the client can publish logs of its activities
========================================================================================================================================================

app\_client = AppClient(logger)

Now we are ready to interact with the client
============================================

1. Lets get all applications

all\_applications = app\_client.get()

1. Lets get an application by name, the app is called "App1"

app\_1 = client.get\_filtered({"app\_name": "App1"})

1. Lets get an application with id 5.

app\_5 = app\_client.get(5)

and, lets get the ID of "App1" in our previous example

app\_1 = client.get\_filtered({"app\_name": "App1"})
app\_1\_id = app\_client.get(app\_1.app\_id)

1. Lets get all applications in Wave3

wave\_filter = {"wave\_name": "Wave3"}
apps\_in\_wave3 = app\_client.get\_filtered(wave\_filter)

1. Lets get all applications in Wave2 and DependencyGroup5

filters = {"wave\_name": "Wave2", "dependency\_group\_name": "DependencyGroup5"}
apps\_in\_wave2\_and\_group5 = app\_client.get\_filtered(filters)

1. Lets create an application
   Note: when using CMF as a data provider, the app\_id is generated automatically, hence not included in the creation attributes below

app1 = {
"app\_name": "App1-Monitoring",
"wave\_name": "Wave3",
"aws\_region": "us-west-2",
"aws\_accountid": "111222333444",
"dependency\_group\_name": "DependencyGroup2"
}

app\_client.create(app1)

1. Lets delete an application with app\_id "App1"

app\_client.delete("App1")
```

How to add a new data client
----------------------------

**1.** Create a new file under `modules/automation_layer/lib/aws_automation_helpers/runbook_data_layer/clients/<new file name>.py`
**2.** Copy the following content into the file, replace `\<resource>` with the new resource name for logging purposes:
```
from typing import Dict, Union, Any, List
from aws\_lambda\_powertools import Logger
from copy import deepcopy

from .base\_client import BaseClient
from ...helpers import filter\_data

class Client(BaseClient):
def **init**(self, logger: Logger):
super().**init**(logger)

```
def get(self, id: str = None):
    self.logger.info(f"Getting <resource> with id: {id}")
    # Implement the function here using one of the data providers

def get_filtered(self, filter_dict: Dict[str, Union[Any, List[Any]]]):
    self.logger.info(f"Getting filtered <resource>s with filter_dict: {filter_dict}")
    # Implement the function here using one of the data providers

def create(self, item: Dict):
    self.logger.info(f"Creating <resource> with item: {item}")
    # Implement the function here using one of the data providers

def delete(self, id: str):
    self.logger.info(f"Deleting <resource> with id: {id}")
    # Implement the function here using one of the data providers


def update(self, id: str, item: Dict):
    self.logger.info(f"Updating <resource> with id: {id} and item: {item}")
    # Implement the function here using one of the data providers
```

`**3.** Implement each function using the availabe data providers
**4.** The newly created DataClient is now ready, to use it, import the file in the automation and initialize the client like so:`
from aws\_automation\_helpers.runbook\_data\_layer.clients. import
new\_client = (logger)

Now the new client is ready to be used
======================================

```

How to add a new data provider
------------------------------

**1.** Create a new file under `modules/automation_layer/lib/aws_automation_helpers/runbook_data_layer/providers/<new file name>.py`
**2.** Copy the following content into the file:
```
from typing import Dict

from aws\_lambda\_powertools import Logger

from .base\_provider import BaseProvider

class Provider(BaseProvider):
logger: Logger = None

```
def __init__(self, logger: Logger):
    self.logger = logger

def get(self, id: str = None):
    self.logger.info(f"Getting item from <Provider> with id: {id}")
    # Implement the function

def create(self, item: Dict):
    self.logger.info(f"Creating item in <Provider>: {item}")
    # Implement the function

def delete(self, id: str):
    self.logger.info(f"Deleting item in <Provider> with id: {id}")
    # Implement the function

def update(self, id: str, item: Dict):
    self.logger.info(f"Updating item in <Provider> with id: {id}: {item}")
    # Implement the function
```

`**3.** Implement each function, use the cmf_provider.py file as a reference
**4.** The DataProvider is now ready to be used by the DataClients, import the provider and initialize in the client and update the functions there as needed`
from ..providers. import

new\_provider = (logger, )

The client can now use the new provider
=======================================

```