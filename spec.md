# Tampere electric buses

## Description

This document describes how measurements from electric buses originally stored
in Wapice IoT-Ticket will be stored to FIWARE.

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
    charging.

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

-   `powerMoving` : Purpose unclear for now.

    -   Attribute type: [Number](https:/schema.org/Number)
    -   Default unit: kilowatt
    -   Attribute metadata:
        -   `timestamp` : Timestamp which captures when the attribute was
            measured.
        -   Type: [DateTime](http://schema.org/DateTime) or `ISO8601` (legacy).
        -   Mandatory
    -   Optional

-   `powerStopped` : Purpose unclear for now.

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

-   `uptime` : Uptime of the measurement device (Wapice WRM 247+).

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
    "id": "vehicle:TKL16",
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
                "value": "2019-04-03T14:52:18.192881"
            }
        }
    },
    "speed": {
        "value": 34.5,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:19.867419"
            }
        }
    },
    "mileageFromOdometer": {
        "value": 99829.875,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:18.527938"
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
                "value": "2019-04-03T14:52:18.578853"
            }
        }
    },
    "power": {
        "value": 75.70000000000027,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:20.218114"
            }
        }
    },
    "chargeState": {
        "value": 87,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:16.938936"
            }
        }
    },
    "powerMoving": {
        "value": 75.70000000000027,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:19.817713"
            }
        }
    },
    "powerStopped": {
        "value": 223.4000000000001,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:16.318142"
            }
        }
    },
    "gear": {
        "value": "drive",
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:15.293451"
            }
        }
    },
    "doorStatus": {
        "value": "closed",
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:19.419983"
            }
        }
    },
    "energyConsumed": {
        "value": 1.9000000000000001,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:16.417363"
            }
        }
    },
    "parkingBrakeEngaged": {
        "value": false,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:18.200178"
            }
        }
    },
    "serviceBrakeAirPressure1": {
        "value": 776,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:16.757913"
            }
        }
    },
    "serviceBrakeAirPressure2": {
        "value": 776,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:16.757913"
            }
        }
    },
    "uptime": {
        "value": 10,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:17.109580"
            }
        }
    },
    "isMoving": {
        "value": true,
        "metadata": {
            "timestamp": {
                "type": "DateTime",
                "value": "2019-04-03T14:52:19.867419"
            }
        }
    }
}
```
