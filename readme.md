# Electric bus data collector

A tool for collecting Tampere electric bus data from IoT-Ticket to FIWARE.
See [spec.md](spec.md) for a description of the FIWARE data model used. The tool can collect historical measurements for the given time period or continuously collect near real time measurements.
It can also be given just a start time for a historical period and after collecting all measurements from
that untill the current time it starts collecting the real time measurements.

## Requirements

- Python 3.7 or higher
- [Requests](https://3.python-requests.org/) library

The version of requests used can be installed with pip:

    pip install -r requirements.txt

## Configuration

Before using the tool it has to be configured by modifying its configuration files in the conf directory.

### collector.json

Determines from what time period measurements are collected. Has the following attributes.

- startDate: Start time for the measurement collection. If not given continuous real time collection is started.
- endDate: End time for the measurment collection. Cannot be in the future. If given the tool will exit after getting all the measurements up to this date.

If there is a startDate but not an endDate measurements from startDate are first collected and after all have been fetched continuous real time collection is started. values for the dates are strings that can be parsed by Python 3.7's [datetime.fromisoformat](https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat) method. For example 2019-06-06T15:34:00.

### iot-ticket.json

IoT-Ticket i.e. the data source configuration:

- url: IoT-Ticket REST API URL ending with rest/v1/
- username: IoT-Ticket account user name
- password: IoT-Ticket account password.

### fiware.json

This configuration file has the fiware Orion and QuantumLeap URLs and also settings how the measurements are sent to FIWARE:

- orion_URL: Orion V2 API URL that ends with /v2/
- quantumleap_URL: QuantumLeap V2 API URL that ends with /v2/
- service: The FIWARE service the measurements are sent to i.e. value of Fiware-Service header in requests.
- service_path: The FIWARE service path the measurments are sent to i.e. the value of Fiware-ServicePath header in the requests.
- custom_headers: Optional setting containing an object with custom header names and values. Can be used with custom API key based authentication.
- update_strategy: Determines what kind of update requests are sent to FIWARE. Following values are supported.
    - small: request contains only one update per entity but can have updates for multiple entities.
    - simple: Request contains all updates for an entity that are available.
    - medium: Similar to simple except there is a maxinum number of updates per request.
- send_to_ql: If true measurement updates are sent directly to QuantumLeap and only the latest values are send to Orion. If false everything is sent to Orion and QuantumLeap is updated using the subscription system of Orion. This can be inefficient and data will probably be lost.
- ql_multiple_notify: Relevant only if sed_to_ql is true. If true the used QuantumLeap instance is expected to [support multiple data elements in notifications](https://github.com/smartsdk/ngsi-timeseries-api/pull/191)
(version 0.6.2 or later). Multiple entity updates are then sent in one request which is the most efficient way to update. Update_strategy medium is then recommended. If value is false only one entity per update request is sent and update strategy small is automatically used.
- update_orion: Relevant only when send_to_ql is true. Determines if Orion is updated at all or if measurements are just sent to QuantumLeap. Useful when collecting older historical data and Orion already has newer updates.
- create_attribute_subscriptions: Relevant only if sed_to_ql is false i.e. measurements to QL are send via Orion subscriptions. If false only one subscription is created so that if any attribute changes all attributes are sent in the notification. If this is true a separate subscription is created for each attribute.

### converter.json

Determines how IoT-Ticket data is converted to FIWARE entities. Normally there is no need to modify this unless you want to change for example from which buses data is collected or which attributes are included.

busIDs attribute has the ids of the IoT-Ticket sites where the bus data is saved to. They are mapped to bus numbers used by the city. The number is used in naming the FIWARE entities. For example bus with number 14 is named Vehicle:TKL14.

The attributes attribute holds an object that defines how values from an IoT-Ticket datanode are converted to entity attributes. A key name is the name of a data node and the object it contains has conversion info. There is at least a name that determines the entity attribute name. Type is the NGSI v2 type. If type is omitted Number is assumed. Mapping is an object that maps the datanode value to a different value. For example door status is indicated with numbers in IoT-Ticket but for the FIWARE entity they are converted to human understandable text e.g. value 0 to open.

### logging.json

Contains configuration settings for log rotating. See the logging section below for details.

- file_max_size_mb: The maximum size of a single log file in megabytes.
- number_of_backups: number of log files kept

## Logging

The tool logs information to the console and two files. The log files will be created to the logs directory. Everythin is logged to the console and log_debug.txt. This includes information about each data collecting from IoT-Ticket and sending it to FIWARE. Log.txt log file contains only info level messages, warnings and errors.

Log rotating is used to limit log sizes. Both log files can grow to  the configured size after which  a copy of the file is made and a new log file started. Configured number of copies of each file is kept. Older logs are deleted.

## Usage

The tool can be used with a local Python installation, with Docker using the included Dockerfile or with docker compose using the included docker-compose.yml.

### Local python

Simply execute the tool's main file:

    python src/main.py
    
### docker

Build the image:

    docker build -t electric-bus .
    
Execute interactively:

    docker run -ti --rm electric-bus
    
Execute in the background:

    docker run -d --name electric-bus electric-bus
    
### docker compose

Simply start with the included compose file:

    docker-compose up -d
    
The compose file connects the conf and logs directories as volumes inside the container. So for example logs are written to the docker host's file system and not inside the container.

## Implementation notes

- IoT-Ticket measurement time stamps are rounded to the nearest second. The original time stamps are mostly unique for each measurement since they are updated separately. Without rounding they would not go nicely to QuantumLeap since internally it creates a separate database row for each time stamp.
- When data is send directly to QuantumLeap only the latest updates are sent to Orion for each measurement collection round. In history collection the duration of this round is 2 hours and in real time 60 seconds.
- When real time collecting there is a short 30 seconds delay between the current time and the period measurements are collected from. This is to ensure that the measurements have arrived to IoT-Ticket.