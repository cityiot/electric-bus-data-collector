# Tampere electric buses

## Description

This document describes how measurements from electric buses originally stored
in Wapice IoT-Ticket are stored to FIWARE. Data is collected from 4 electric buses and one hybrid bus operating on the same
bus line. The line is line 2 operating between Pyynikintori and Rauhamiemi which takes about 20 minutes. Overall 18 different measurements are available. Measurements collected include speed, location as latitude and
longitude, battery charge state percent, power, energy consumed, brace air
pressure and door status. However not all measurements are available for all
buses most notably only speed and location are available from the hybrid bus
due to issues with configuring the collection device. The measurements are sent to the IoT-Ticket in
real time through Wapice's proprietary hardware which is connected to the bus
systems. The update interval for the measurements varies. Some measurements such
as charge state and door status are updated about every 5 seconds while some
others such as location and speed are updated about every second.

Measurements are transfered from IoT-Ticket to FIWARE in near real time. Measurements from a period of one  minute at a time are collected from IoT-Ticket and send to FIWARE with the newest values for all attributes going to Orion and everything going to Quantumleap. There is a 60 second delay for this collection to ensure that all measurements have arrived to IoT-Ticket. The timestamps are rounded to second precision from the microsecond precision used by IoT-Ticket. As of this writing on 2019-10-28 the data collection is on going and measurements are available from the beginning of this year.
 
## Data Model

The data model is based on the official FIWARE
[Vehicle data model](https://fiware-datamodels.readthedocs.io/en/latest/Transportation/Vehicle/Vehicle/doc/spec/index.html)
with some custom attributes added. First attributes used fromt he official model
with original descriptions are listed here with some additional notes. Then
attributes added to the model are described.

### Vehicle attributes

-   `id` : Entity's unique identifier.

    -   Notes: The form used here is Vehicle:name.

-   `type` : Entity type. It must be equal to `Vehicle`.

-   `source` : A sequence of characters giving the source of the entity data.

    -   Attribute type: Text or URL
    -   Notes: IoT-Ticket REST API URI for the site representing the bus.
    -   Optional

-   `name` : Name given to this vehicle.

    -   Normative References: [https://schema.org/name](https://schema.org/name)
    -   Notes: same as fleetVehicleId
    -   Optional

-   `vehicleType` : Type of vehicle from the point of view of its structural
    characteristics. This is different than the vehicle category (see below).

    -   Attribute type: [Text](https://schema.org/Text)
    -   Allowed Values: The following values defined by _VehicleTypeEnum_ and
        _VehicleTypeEnum2_,
        [DATEX 2 version 2.3](http://d2docs.ndwcloud.nu/_static/umlmodel/v2.3/index.htm):
        -   (`agriculturalVehicle`, `bicycle`, `bus`, `minibus`, `car`,
            `caravan`, `tram`, `tanker`, `carWithCaravan`, `carWithTrailer`,
            `lorry`, `moped`, `tanker`, `motorcycle`, `motorcycleWithSideCar`,
            `motorscooter`, `trailer`, `van`, `caravan`,
            `constructionOrMaintenanceVehicle`)
        -   (`trolley`, `binTrolley`, `sweepingMachine`, `cleaningTrolley`)
    -   Notes: Here value is always bus
    -   Mandatory

-   `category` : Vehicle category(ies) from an external point of view. This is
    different than the vehicle type (car, lorry, etc.) represented by the
    `vehicleType` property.

    -   Attribute type: List of [Text](https:/schema.org/Text)
    -   Allowed values:
        -   (`public`, `private`, `municipalServices`, `specialUsage`).
        -   (`tracked`, `nonTracked`). Tracked vehicles are those vehicles which
            position is permanently tracked by a remote system.
        -   Or any other needed by an application They incorporate a GPS
            receiver together with a network connection to periodically update a
            reported position (location, speed, heading ...).
    -   Notes: Value is always list with public and tracked
    -   Mandatory

-   `location` : Vehicle's last known location represented by a GeoJSON Point.
    Such point may contain the vehicle's _altitude_ as the third component of
    the `coordinates` array.

    -   Attribute type: `geo:json`.
    -   Normative References:
        [https://tools.ietf.org/html/rfc7946](https://tools.ietf.org/html/rfc7946)
    -   Attribute metadata:
        -   `timestamp`: Timestamp which captures when the vehicle was at that
            location. This value can also appear as a FIWARE
            [TimeInstant](https://github.com/telefonicaid/iotagent-node-lib/blob/master/README.md#the-timeinstant-element)
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Mandatory only if `category` contains `tracked`.
    -   Notes: Altitude is not included here.

-   `speed` : Denotes the magnitude of the horizontal component of the vehicle's
    current velocity and is specified in Kilometers per Hour. If provided, the
    value of the speed attribute must be a non-negative real number. `null`
    _MAY_ be used if `speed` is transiently unknown for some reason.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: Kilometers per hour
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the vehicle was moving
            at that speed. This value can also appear as a FIWARE
            [TimeInstant](https://github.com/telefonicaid/iotagent-node-lib/blob/master/README.md#the-timeinstant-element)
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Mandatory only if `category` contains `tracked`.

-   `fleetVehicleId` : The identifier of the vehicle in the context of the fleet
    of vehicles to which it belongs.

    -   Attribute Type: [Text](https://schema.org/Text)
    -   Notes: These are of the form TKLxxx where xxx is a number e.g. TKL16
    -   Mandatory if neither `vehiclePlateIdentifier` nor
        `vehicleIdentificationNumber` is defined.

-   `mileageFromOdometer` : The total distance travelled by the particular
    vehicle since its initial production, as read from its odometer.

    -   Normative References:
        [https://schema.org/mileageFromOdometer](https://schema.org/mileageFromOdometer)
    -   Attribute metadata:
        -   `timestamp`: Timestamp associated to this measurement. This value
            can also appear as a FIWARE
            [TimeInstant](https://github.com/telefonicaid/iotagent-node-lib/blob/master/README.md#the-timeinstant-element)
            -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601`
                (legacy).
            -   Mandatory
    -   Optional
    -   Notes: unit is kilometers

-   `serviceProvided` : Service(s) the vehicle is capable of providing or it is
    assigned to.

    -   Attribute type: List of [Text](https:/schema.org/Text)
    -   Allowed values: (`garbageCollection`, `parksAndGardens`, `construction`,
        `streetLighting`, `roadSignalling`, `cargoTransport`, `urbanTransit`,
        `maintenance`, `streetCleaning`, `wasteContainerCleaning`,
        `auxiliaryServices` `goodsSelling`, `fairground`, `specialTransport`) or
        any other value needed by an specific application.
    -   Optional
    -   Notes: value is list containing urbanTransit

-   `dateModified` : Last update timestamp of this entity.

    -   Attribute type: [DateTime](https://schema.org/DateTime)
    -   Read-Only. Automatically generated.

-   `dateCreated` : Creation timestamp of this entity.
    -   Attribute type: [DateTime](https://schema.org/DateTime)
    -   Read-Only. Automatically generated.

The following vehicle attributes are not used:

-   dataProvider
-   description
-   previousLocation
-   heading
-   cargoWeight
-   vehicleIdentificationNumber
-   vehiclePlateIdentifier
-   dateVehicleFirstRegistered
-   dateFirstUsed
-   purchaseDate
-   vehicleConfiguration
-   color
-   owner
-   feature
-   vehicleSpecialUsage
-   refVehicleModel
-   areaServed
-   serviceStatus

### Custom attributes

-   `airTemperature` : Air temperature outside the bus.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: Degrees centigrades.
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `power` : Power used from the bus battery. If this is negative the bus is
    charging either from the grid or from braking.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: kilowatt
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `chargeState` : State of bus battery charge as percents from the maximum
    charge.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: percent
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `powerMoving` : Same as power except measured only when the bus is moving.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: kilowatt
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `powerStopped` : Same as power except measured only when the bus is stopped.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: kilowatt
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `gear` : Selected drive mode.

    -   Attribute type: [Text](https://schema.org/Text)
    -   Allowed values: reverse, neutral, drive
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `doorStatus` : State of the bus doors.

    -   Attribute type: [Text](https://schema.org/Text)
    -   Allowed values:
        -   open: at least one door open
        -   closing: Last door closing.
        -   closed: All doors closed.
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `energyConsumed` : Energy consumed since the bus was last started. Possibily
    since `uptime`´hours.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: kilowatthour
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `parkingBrakeEngaged` : Is the parking brake in use.

    -   Attribute type: [Boolean](https://schema.org/Boolean)
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `satellites` : Number of GPS satellites in use by the positioning system.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `serviceBrakeAirPressure1` : Air pressure of a brake.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: kilopascals
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `serviceBrakeAirPressure2` : Air pressure of a brake.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: kilopascals
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `uptime` : Uptime of the measurement device (Wapice WRM 247+). Note only full hours are reported i.e. these are allways integers.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: hour
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `isMoving` : Is the bus moving.

    -   Attribute type: [Boolean](https://schema.org/Boolean)
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

## Examples

### Normalized Example

Normalized NGSI response

```json
{
    "id": "Vehicle:TKL16",
    "type": "Vehicle",
    "source": {
        "value": "https://iot-ticket.tamk.cloud/rest/v1/sites/1911"
    },
    "category": {
        "value": ["public", "tracked"]
    },
    "vehicleType": {
        "value": "bus"
    },
    "name": {
        "value": "TKL16"
    },
    "fleetVehicleId": {
        "value": "TKL16"
    },
    "location": {
        "type": "geo:json",
        "value": {
            "type": "Point",
            "coordinates": [23.769203333333333, 61.49531666666667]
        },
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:18.192881Z"
            }
        }
    },
    "speed": {
        "value": 34.5,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:19.867419Z"
            }
        }
    },
    "mileageFromOdometer": {
        "value": 99829.875,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:18.527938Z"
            }
        }
    },
    "serviceProvided": {
        "value": ["urbanTransit"]
    },
    "airTemperature": {
        "value": 10.9062,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:18.578853Z"
            }
        }
    },
    "power": {
        "value": 75.70000000000027,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:20.218114Z"
            }
        }
    },
    "chargeState": {
        "value": 87,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:16.938936Z"
            }
        }
    },
    "powerMoving": {
        "value": 75.70000000000027,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:19.817713Z"
            }
        }
    },
    "powerStopped": {
        "value": 223.4000000000001,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:16.318142Z"
            }
        }
    },
    "gear": {
        "value": "drive",
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:15.293451Z"
            }
        }
    },
    "doorStatus": {
        "value": "closed",
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:19.419983Z"
            }
        }
    },
    "energyConsumed": {
        "value": 1.9000000000000001,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:16.417363Z"
            }
        }
    },
    "parkingBrakeEngaged": {
        "value": false,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:18.200178Z"
            }
        }
    },
    "serviceBrakeAirPressure1": {
        "value": 776,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:16.757913Z"
            }
        }
    },
    "serviceBrakeAirPressure2": {
        "value": 776,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:16.757913Z"
            }
        }
    },
    "uptime": {
        "value": 10,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:17.109580Z"
            }
        }
    },
    "isMoving": {
        "value": true,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:19.867419Z"
            }
        }
    }
}
```

## Accessing the data

The measurements are stored in the Tampere University CityIoT FIWARe platform: <https://tlt-cityiot.rd.tuni.fi>
The used FIWARE service is public_transport and all bus entities are under the /tampere/electric_bus service path.

### Example requests

A few example curl commands for getting the data. Replace your_apikey with a api key that has at least read access to public_transport service.

Get all bus entities with their attributes from Orion:

    curl -H 'Fiware-Service: public_transport' -H 'Fiware-ServicePath: /Tampere/electric_bus' -H 'apikey: your_apikey' "https://tlt-cityiot.rd.tuni.fi/orion/v2/entities"

Get the power and speed of bus with id Vehicle:TKL15 from Orion:
    
    curl -H 'Fiware-Service: public_transport' -H 'Fiware-ServicePath: /Tampere/electric_bus' -H 'apikey: your_apikey' "https://tlt-cityiot.rd.tuni.fi/orion/v2/entities/Vehicle:TKL15?attrs=speed,power"

Get all values for power and speed for TKL15 between 14:01 and 14:02 on 28th of October 2019 from quantumleap:
 
    curl -H 'Fiware-Service: public_transport' -H 'Fiware-ServicePath: /Tampere/electric_bus' -H 'apikey: your_apikey' "https://tlt-cityiot.rd.tuni.fi/quantumleap/v2/entities/Vehicle:TKL15?attrs=speed,power&&fromDate=2019-10-28T12:01:00&&toDate=2019-10-28T12:02:00"

Note: times above are UTC time.