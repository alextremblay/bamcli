#!/usr/local/bin/python3 -tt

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4


'''

RESTful Python API for BAM
REST WADL: https://proteus.utoronto.ca/Services/REST/application.wadl

From JumpStart to BAM
User Group Webinar - Making APIs Work for You - Episode 1

- Web Layer and API Layer

	Connect -> Login -> API Calls -> Logout

	SOAP one session, and then at end closes

	REST single shot sessions as request and responses

	URLs contain action verbs: Service, Create, Read, Update, Delete

	API account is the same as a normal user account (hybrid as well)

- Logs -> /var/log/Server.log

- API calls are small unit operations each with custom input and output

- To send NULL values use e.g. var = ''

- BAM v8.1.0 and present support REST

- Sequence of steps for the REST API to e.g. add a host record to bozo.utoronto.ca

    a. Get the REST onetime Token, add it to the https Header
    b. Get the Parent Configuration object by name
    c. Get the Parent View object by name
    d. Get the Parent Zone object by name, using the fqdn (i.e. utoronto.ca)


'''

import os
import sys
import json
import requests

'''

Global Variables convention:
    * start with UpperCase
    * have no _ character
    * may have mid UpperCase words

'''

Debug = True
Debug = False

BaseURL = ''

ConfigId = 0
ViewId = 0


LegalTLDs = ('ca', 'com', 'edu', 'org')

AuthHeader = {}

ObjectTypes = (
        'Entity',
        'Configuration',
        'View',
        'InternalRootZone',
        'ExternalHostRecord'
        'Zone',
        'HostRecord',
        'AliasRecord',
        'MXRecord',
        'TXTRecord',
        'SRVRecord',
        'GenericRecord',
        'HINFORecord',
        'NAPTRRecord',
        'StartOfAuthority',
)

RRObjectTypes = ObjectTypes[5:]

RRTypeMap = {
        'MX': {'obj_type': 'MXRecord', 'prop_key': 'linkedRecordName'},
        'A': {'obj_type': 'HostRecord', 'prop_key': 'addresses'},
        'a': {'obj_type': 'GenericRecord', 'prop_key': 'rdata'},
        'PTR': {'obj_type': 'GenericRecord', 'prop_key': 'rdata'},
        'CNAME': {'obj_type': 'AliasRecord', 'prop_key': 'linkedRecordName'},
        'TXT': {'obj_type': 'TXTRecord', 'prop_key': 'txt'},
}

BAM2Bind = {
        'HostRecord': 'A',
        'MXRecord': 'MX',
        'AliasRecord': 'CNAME',
        'TXTRecord': 'TXT',
}

IPv4Objects = (
        'IP4Block',
        'IP4Network',
        'IP4Adress',
        'IP4DHCPRange',
        'IP4NetworkTemplate',
)

Categories = {
    'all': 'ALL',
    'admin': 'ADMIN',
    'Configuration': 'CONFIGURATION',
    'deploymentOptions': 'DEPLOYMENT_OPTIONS',
    'deploymentRoles': 'DEPLOYMENT_ROLES',
    'deploymentSchedulers': 'DEPLOYMENT_SCHEDULERS',
    'dhcpClassObjects': 'DHCPCLASSES_OBJECTS',
    'dhcpNACPolicies': 'DHCPNACPOLICY_OBJECTS',
    'IP4Objects': 'IP4_OBJECTS',
    'IP6Objects': 'IP6_OBJECTS',
    'MACPoolObjects': 'MACPOOL_OBJECTS',
    'resourceRecords': 'RESOURCE_RECORD',
    'servers': 'SERVERS',
    'tags': 'TAGS',
    'tasks': 'TASKS',
    'TFTPObjects': 'TFTP_OBJECTS',
    'vendorProfiles ': 'VENDOR_PROFILES',
    'viewZones ': 'VIEWS_ZONES',
    'TSIGKeys ': 'TSIG_KEYS',
    'GSS': 'GSS',
    'DHCPZones': 'DHCP_ZONES',
    'ServerGroup': 'SERVERGROUP',
}


'''

Generic API Methods

* use the UPDATE, DELETE and GET methods
* are used in many Address Manager API scripts


Getting Objects:

Generic methods for getting entity values.
*  Get entities by name
*  Get entities by ID
*  Get Entities
*  Get Parent

See the BAM API Guide, Chapter 4

'''


'''
Get Entity by Name

Returns objects from the database referenced by their name field.

Output / Response: Returns the requested object from the database.

APIEntity getEntityByName( long parentId, String name, String type )

Parameter Description
 parentId The ID of the target object’s parent object.
 name The name of the target object.
 type The type of object returned by the method.
 This string must be one of the constants listed in ObjectTypes

'''


def get_entity_by_name(id, name, type):
    URL = BaseURL + 'getEntityByName'
    params = {'parentId': id, 'name': name, 'type': type}
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()
    

'''

Get Entity by ID

Returns objects from the database referenced by their database ID
and with its properties fields populated.

Output / Response
    Returns the requested object from the database with its properties fields populated.
    For more information about the available options, refer to IPv4Objects
    on page 248 in the Property Options Reference section.

Returns E.g.

{
    'id': 2217650,
    'name': 'utoronto',
    'properties': 'deployable=true|absoluteName=utoronto.ca|',
    'type': 'Zone'
}

'''


def get_entity_by_id(entityid):
    URL = BaseURL + 'getEntityById'
    params = {'id': str(entityid)}
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()


'''

Get Entities

Returns an array of requested child objects for a given parentId value.
Some objects returned in the array may not have their properties field set.
For those objects, you will need to call them individually using
the getEntityById() method to populate the properties field.

* Using getEntities() to search users will return all users existing in Address Manager.
  Use getLinkedEntities() or linkEntities() to search users under a specific user group.

* Using getEntities() to query server objects in configurations containing XHA pairs might
result in a connection timeout if any of the servers in an XHA pair are not reachable.

Output / Response
    Returns an array of the requested objects from the database without their
    properties fields populated, or returns an empty array.

API call:
    getEntities( long parentId, String type, int start, int count )

Parameter Description:
    parentId: The object ID of the target object’s parent object.
    type: The type of object returned.
          This must be one of the constants listed in Object Types
    start:  Indicates where in the list of objects to start returning objects.
            The list begins at an index of 0.
    count:  Indicates the maximum number of child objects to return.
            defaults to 10

Returns a list of branch items given the root one level up

'''

def get_entities(parentid, type, start=0, count=10):
    URL = BaseURL + 'getEntities'
    params = {'parentId': parentid, 'type': type, 'start': start, 'count': count}
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()


'''

Get Parent
    Returns the parent entity of a given entity (referenced by Id).

Output / Response
    Returns the APIEntity for the parent entity with its properties fields populated.
    For more information about the available options, refer to IPv4Objects
    on page 248 in the Property Options Reference section.

E.g. parent object:

{
    'id': 217650,
    'name': 'utoronto',
    'type': 'Zone',
    'properties': 'deployable=true|absoluteName=utoronto.ca|'
}

'''


def get_parent(childid):
    URL = BaseURL + 'getParent'
    params = {'entityId': str(childid)}
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()


'''

Generic methods for searching and retrieving entities.

    * Custom Search
    * Search by Category
    * Search by Object Types
    * Get Entities by Name
    * Get Entities by Name Using Options
    * Get MAC Address

Supported wildcards in the search string:
You can use the following wildcards when invoking a search method. These wildcards are supported only
in the String parameter:

    * ^ matches the beginning of a string. For example, ^ex matches example but not text.
    * $ matches the end of string. For example: ple$ matches example but not please.
    * * matches zero or more characters within a string. For example: ex*t matches exit and excellent.

Note: You cannot use the following characters in the search string:

    * , (comma)
    * ‘ (single quotation mark)
    * ( ) (parentheses)
    * [ ] (square brackets)
    * { } (braces)
    * % (percent)
    * ? (question mark)
    * + (addition/plus sign)

'''

'''

Custom Search
    Search for an array of entities by specifying object properties.

Output / Response
    Returns an array of APIEntities matching the specified object properties or returns an empty array.
    The APIEntity will at least contain Object Type, Object ID, Object Name, and Object Properties.

API call:
    APIEntity[]
    customSearch ( String[] filters, String type, String[] options, int start, int count)

    filters: List of properties on which the search is based.  Valid format is: name=value, name2=value2
             E.g. filters=filter1=abc&filters=filter2=def

    type: The object type that you wish to search. The type cannot be null or empty string ""
          This must be one for the following object types:

            * IP4Block
            * IP4Network
            * IP4Addr
            * GenericRecord
            * HostRecord
            * Any other objects with user-defined fields

    options: A list of strings of search options specifying the search behavior.
             Reserved for future use.
             E.g. options=option1=val1&options=option2=val2

    start: Indicates where in the list of returned objects to start returning objects.
           The value must be a non-negative value and cannot be null or empty

    count: The maximum number of objects to return.
           The value must be a positive value between 1 and 1000.
           This value cannot be null or empty.

    Supported fields/filters for each type:

        Type: GenericRecord
        Fields:
            * comments=Text
            * ttl=Long
            * recordType=Text
            * rdata=Text

        Type: HostsRecord
        Fields:
            * comments=Text
            * ttl=Long
        
        Type: IP4Block
        Fields:
            * inheritDNSRestrictions=Boolean
            * pingBeforeAssign=Boolean
            * reverseZoneSigned=Boolean
            * allowDupHost=Boolean
            * inheritDefaultDomains=Boolean
            * highwatermark=Integer
            * lowwatermark=Integer

        Type: IP4Network
        Fields:
            * inheritDNSRestrictions=Boolean
            * pingBeforeAssign=Boolean
            * reverseZoneSigned=Boolean
            * allowDupHost=Boolean
            * inheritDefaultDomains=Boolean
            * portInfo=Text
            * highwatermark=Integer
            * lowwatermark=Integer

        Type: IP4Addr
        Fields:
            * routerPortInfo=Text
            * portInfo=Text
            * vlanInfo=Text

API Example:
    http://<AddressManager_ip>/Services/REST/customSearch?
    filters=filter1=abc&filters=filter2=def&type=IP4Block&options=&start=0&count=10

The filters and options should be sent using the follows Requests data structure:

    'filters': ['comments=This is important', 'recordType=MX', 'ttl=86400', 'rdata=128.100.103.*']

The return is a list as follows

[
    {'id': 2429335, 'name': '',
      'properties': 'ttl=86400|absoluteName=theta.utoronto.ca|linkedRecordName=alt2.aspmx.l.google.com|priority=5|',
      'type': 'MXRecord'},
    {'id': 2429340, 'name': '',
      'properties': 'ttl=86400|absoluteName=lcd.utoronto.ca|linkedRecordName=aspmx3.googlemail.com|priority=10|',
      'type': 'MXRecord'},
    {'id': 2429341, 'name': '',
      'properties': 'ttl=86400|absoluteName=lcd.utoronto.ca|linkedRecordName=aspmx2.googlemail.com|priority=10|',
      'type': 'MXRecord'}
]


'''

def custom_search(filters, type, start=0, count=10):
    URL = BaseURL + 'customSearch'
    params = {
            'filters': filters,
            'type': type,
            'options': '',
            'start': start,
            'count': count,
    }
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()


'''

Search by Category:

    Returns an array of entities by searching for keywords associated with objects
    of a specified object category.

Output / Response:
    Returns an array of entities matching the keyword text and the category type,
    or returns an empty array.

API call:
    APIEntity[] searchByCategory ( String keyword, String category, int start, int count )

Parameter Description:
    keyword: The search keyword string. This value cannot be null or empty.
    
    category: The entity category to be searched. This must be one of the entity categories
              listed in Categories dictionary
              
    start: Indicates where in the list of returned objects to start returning objects.
           The list begins at an index of 0. This value cannot be null or empty.
           
    count: The maximum number of objects to return. The default value is 10.
           This value cannot be null or empty.


'''

def search_by_category(key, category, start=0, count=10):
    URL = BaseURL + 'searchByCategory'

    params = {
        'keyword': key,
        'category': category,
        'start': start,
        'count': count
    }

    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()


'''

Search by Object Types

Returns an array of entities by searching for keywords associated with objects of a specified object type.
You can search for multiple object types with a single method call.

Output / Response
Returns an array of entities matching the keyword text and the category type, or returns an empty array.

Arguments in the parameter list:

keyword: The search string. Can not be NULL or Empty
        ^ matches the beginning of a string
        $ matches the end of a string
        * matches one or more characters within a string

types: The object types for which to search in the format type1,type2,[type3 ...]
       See ObjectTypes list E.g.
        'Entity','Configuration','View','Zone','HostRecord','MXRecord',

start: List index (starting with 0) to mark the beginning of the return

count: Maximum values to return. Default is 10


'''


def search_by_object_types(key, types, start=0, count=10):
    URL = BaseURL + 'searchByObjectTypes'
    params = {
        'keyword': key,
        'types': types,
        'start': start,
        'count': count
    }
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()


'''

Get Entities by Name

Returns an array of entities that match the specified parent, name, and object type.

Output / Response:  Returns an array of entities.
                    The array is empty if there are no matching entities.
API call:

APIEntity getEntitiesByName (long parentId, String name, String type, int start, int count )

Parameter Description
    parentId: The object ID of the parent object of the entities to be returned.
    name: The name of the entity.
    types:  The type of object to be returned. This value must be one of the object types
            listed in Object Types on page 209.
    start:  Indicates where in the list of returned objects to start returning objects.
            The list begins at an index of 0. This value cannot be null or empty.
    count: The maximum number of objects to return. The default value is 10.
           This value cannot be null or empty.

'''


def get_entities_by_name(parentid, name, obj_type, start=0, count=10):
    URL = BaseURL + 'getEntitiesByName'
    params = {
        'parentId': parentid,
        'name': name,
        'type': obj_type,
        'start': start,
        'count': count,
    }
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()

'''

Get Entities by Name Using Options

Returns an array of entities that match the specified name and object type. Searching behavior can be
changed by using the options.

Output / Response
Returns an array of entities. The array is empty if there are no matching entities.

API call:
APIEntity[] getEntitiesByNameUsingOptions ( long parentId, String name, String type, int
start, int count, String options )

Parameters:

    Parameters:

    parentId: The object ID of the parent object of the entities to be returned.
    name:   The name of the entity.
    types:  The type of object to be returned. This value must be one of the object types listed
            in Object Types
    start:  Indicates where in the list of returned objects to start returning objects. The list
            begins at an index of 0. This value cannot be null or empty.
    count:  The maximum number of objects to return. The default value is 10. This value
            cannot be null or empty.
    options: A string containing options. Currently the only available option is
            ObjectProperties.ignoreCase. By default, the value is set to false. Setting this
            option to true will ignore the case-sensitivity used while searching entities by name.

            ObjectProperties.ignoreCase = [true | false]

'''

def get_entities_by_name_using_options(parentid, name, typ, options='false', start=0, count=10):
    URL = BaseURL + 'getEntitiesByNameUsingOptions'
    params = {
        'parentId': parentid,
        'name': name,
        'type': type,
        'start': start,
        'count': count,
        'options': options,
    }
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()

'''

Get MAC Address

Returns an APIEntity for a MAC address.

Output / Response
Returns an APIEntity for the MAC address. Returns an empty APIEntity if the MAC address does not exist.
The property string of the returned entity should include the MAC address:
    address=nn-nn-nn-nn-nn-nn|
If the MAC address is in a MAC pool, the property string includes the MAC pool information:
    macPool=macPoolName|

API call:
APIEntity getMACAddress ( long configurationId, String macAddress )

Parameter Description
    configurationId: The object ID of the configuration in which the MAC address is located.
    macAddress: The MAC address in the format nnnnnnnnnnnn, nn-nn-nn-nn-nn-nn or
                nn:nn:nn:nn:nn:nn, where nn is a hexadecimal value.

'''

def get_MAC_Address(confid, macaddr):
    URL = BaseURL + 'getMACAddress'
    params = {
        'configurationId': confid,
        'macAddress': macaddr,
    }
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()



'''

Updating Objects

    Generic methods for updating an object.
    Updating an object involves two steps:
        1. Building the object or parameter string used to update the object.
        2. Performing the update.

Update: Updates entity objects.

API call: All entity update statements follow this format:

    void update ( APIEntity entity )

Parameter Description

entity: The actual API entity passed as an entire object that has its mutable
        values updated

'''

def update(entity):
    URL = BaseURL + 'update'
    req = requests.put(URL, headers=AuthHeader, json=entity)

'''

Update with Options

Updates objects requiring a certain behavior that is not covered by the regular update() method. This
method is currently used for CName, MX and SRV records, and the option is only applicable to these
types.

Output / Response: None

API call:
void updateWithOptions ( APIEntity entity, String options )

Parameter Description

    entity: The actual API entity to be updated.

    options: A string containing the update options. Currently, only one option is
             supported:

                linkToExternalHost=boolean

            If true, update will search for the external host record specified in
            linkedRecordName even if a host record with the same exists under the same DNS View.
            If the external host record is not present, it will throw an exception.
            
            If false, update will search for the host record specified in linkedRecordName

'''

def update_with_options(ent, opts):
    URL = BaseURL + 'updateWithOptions'
    req = requests.put(URL, headers=AuthHeader, json=ent)
    return req.json()


'''

Deleting Objects

Generic methods for deleting an object.
There are two generic methods for getting entity values:
    * Delete
    * Delete with Options

Delete:
    Deletes an object using the generic delete() method.
    
Output / Response:
    None.
    
API call:
    Pass the entity ID from the database identifying the object to be deleted.
    void delete ( long ObjectId )

Parameter Description:
    ObjectId The ID for the object to be deleted.

Output / Response
    None

'''

def delete(obj_id):
    URL = BaseURL + 'delete'
    param = {'objectId': obj_id}
    req = requests.delete(URL, headers=AuthHeader, params=param)
    
'''

Delete with Options
    Deletes objects that have options associated with their removal.
    This method currently works only with the deletion of dynamic records
    from the Address Manager database. When deleted, dynamic records present
    the option of not dynamically deploying to DNS/DHCP Server.
Output / Response
    None.

'''
    

def delete_with_options(obj_id, options):
    URL = BaseURL + 'deleteWithOptions'
    params = {
        'objectId': obj_id,
        'options': options
    }
    req = requests.delete(URL, headers=AuthHeader, params=params)


'''

Linked Entities

Generic methods for getting, link or unlink entities.

    * Get Linked Entities
    * Link Entities
    * Unlink Entities

'''

'''

Get Linked Entities

Returns an array of entities containing the entities linked to a specified entity.
The array is empty if there are no linked entities.

Output / Response
Returns an array of entities. The array is empty if there are no linked entities.

API call:
APIEntity[] getLinkedEntities ( long entityId, String type, int start, int count)

Parameter Description
    entityId: The object ID of the entity for which to return linked entities.

    type:   The type of linked entities which need to be returned.
            This value must be one of the types listed in Object Types on page 209.

! Attention:
    * While specifying a resource record as the entityId, if you want to find
    all the records (CNAME, MX, or SRV records) having links to this
    record, you can use RecordWithLink for the type parameter.

    * When specifying a MAC address as the entityId, this method
    returns the IPv4 address associated with the MAC address. When
    appropriate, leaseTimeand expiryTimeinformation also appears in
    the returned properties string.

    start: Indicates where in the list of returned objects to start returning objects.
           The list begins at an index of 0. This value cannot be null or empty.

    count: The maximum number of objects to return.

'''

def get_linked_entities(entityid, obj_type, start=0, count=10):
    URL = BaseURL + 'getLinkedEntities'

    params = {
            'entityId': entityid,
            'type': obj_type,
            'start': start,
            'count': count,
    }

    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()
    
'''

Link Entities
    Establishes a link between two specified Address Manager entities.
Output / Response
    None.

API call:
void linkEntities ( long entity1Id, long entity2Id, String properties )

Parameter Description:

entity1Id: The object ID of the first entity in the pair of linked entities.
entity2Id: The object ID of the second entity in the pair of linked entities.
properties: Adds object properties, including user-defined fields.


'''

def link_entities(entity1id, entitity2id, properties):
    URL = BaseURL + 'linkEntities'
    
    params = {
        'entity1Id': entity1id,
        'entity2Id': entity2id,
        'properties': properties
    }
    
    req = requests.put(URL, headers=AuthHeader, params=params)
    return req.json()

'''
Unlink Entities
    Removes the link between two specified Address Manager entities.
    
Output / Response
    None.

This method works on the following types of objects and links:
    Type of entity1Id   Type of entity2Id   Result
    Any entity          Tag                 Removes the tag linked to the entity.
    MACPool             MACAddress          Removes MAC address from MAC pool.
    MACAddress          MACPool             Removes Mac Pool from MAC address.
    User                UserGroup           Removes Group from User
    UserGroup           User                Removes User from Group
    etc...


'''


def unlink_entities(entity1id, entitity2id, properties):
    URL = BaseURL + 'unlinkEntities'
    
    params = {
        'entity1Id': entity1id,
        'entity2Id': entity2id,
        'properties': properties
    }
    
    req = requests.put(URL, headers=AuthHeader, params=params)
    return req.json()

'''

IPAM Functions

Add IPv4 Block by CIDR
    Adds a new IPv4 Block using CIDR notation.

Output / Response
    Returns the object ID for the new IPv4 block.

API call:
    long addIP4BlockByCIDR ( long parentId, String CIDR, String properties )
    
Parameter Description:
    parentId: The object ID of the target object’s parent object.
    CIDR: The CIDR notation defining the block (for example, 10.10/16).
    properties: A string containing options. For more information about the available
                options, refer to IPv4Objects on page 248 in the
                Property Options Reference section.


'''

'''

Assign IPv4 Address
    Assigns a MAC address and other properties to an IPv4 address.

Output / Response
    Returns the object ID for the newly assigned IPv4 address.

API call:
    long assignIP4Address (
        long configurationId, 
        String ip4Address, 
        String macAddress,
        String hostInfo,
        String action,
        String properties
    )

Parameter: Description

configurationId:
    The object ID of the configuration in which the IPv4 address is located.

ipv4Address:
    The IPv4 address.

macAddress:
    The MAC address to assign to the IPv4 address. The MAC address
    can be specified in the format:
        nnnnnnnnnnnn, nn-nn-nn-nn-nn-nn or nn:nn:nn:nn:nn:nn,
        where nn is a hexadecimal value.

hostInfo:
    A string containing host information for the address in the following format:
        hostname,viewId,reverseFlag,sameAsZoneFlag,
        hostname,viewId,reverseFlag,sameAsZoneFlag,
        hostname,viewId,reverseFlag,sameAsZoneFlag
    Where:
        hostname - FQDN for host record to be added
        viewId - object ID of the view under which this host should be created
        reverseFlag - flag indicating if a reverse should be created (true|false)
        sameAsZoneFlag - The flag indicating if record should be created as same
            as zone record. The possible values are true and false
    The comma-separated parameters may be repeated in the order shown above.
    The string must not end with a comma.

action:
    This parameter must be set to the constants in IP Assignment Action Values:
        MAKE_STATIC, MAKE_RESERVED or MAKE_DHCP_RESERVED

properties:
    A string containing the following property, including user-defined fields:

        ptrs:
            a string containing the list of unmanaged external host records to
            be associated with the IPv4 address in the following format:
                viewId,exHostFQDN[, viewId,exHostFQDN,...]

            EntityProperties props = new EntityProperties();
            props.addProperty(
                ObjectProperties.ptrs,
                123,exHostFQDN.com,456,exHostFQDN.net"
            )
            long addressId =
                service.assignIP4Address(
                    configurationId,
             IPv4Address, macAddressStr, hostInfo,
         IPAssignmentActionValues.MAKE_STATIC, props.getPropertiesString() );

 name -- name of the IPv4 address.

    locationCode - the hierarchical location code consists of a set of 1 to 3
    alpha-numeric strings separated by a space. The first two characters
    indicate a country, followed by next three characters which indicate
    a city in UN/ LOCODE. New custom locations created under a UN/LOCODE
    city are appended to the end of the hierarchy. For example, CA TOR
    OF1 indicates: CA= Canada TOR=Toronto OF1=Office 1.

    The code is case-sensitive. It must be all UPPER CASE letters.
    The country code and child location code should be alphanumeric strings.


'''

def assign_IP4_Address(configid, ipaddr, macaddr, hostinfo, action, props):
    URL = BaseURL + 'assignIP4Address'

    params = {
        'configurationId': configid,
        'ip4Address': ipaddr,
        'macAdress': macaddr,
        'hostInfo': hostinfo,
        'action': action,
        'properties': props
    }

    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()


def add_IP4_block_by_CIDR(parentid, cidr, properties):
    URL = BaseURL + 'addIP4BlockByCIDR'
    
    params = {
        'parentId': parentid,
        'CIDR': cidr,
        'properties': properties
    }
    
    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()


def get_ip4_address(ip):
    URL = BaseURL + 'getIP4Address'
    params = {'containerId': ConfigId, 'address': ip}
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()

def get_ipranged_by_ip(ip):
    URL = BaseURL + 'getIPRangedByIP'
    params = {
            'containerId': ConfigId,
            'type': 'IP4Network',
            'address': ip
    }
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()


def assign_ip4Address(config_id, ip_addr, mac_addr, host_info, action, props):
    URL = BaseURL + 'assignIP4Address'
    params = {
        'configurationId': config_id,
        'ip4Address': ip_addr,
        'macAddress': mac_addr,
        'hostInfo': host_info,
        'action': action,
        'properties': props
    }
    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()

'''

Low level functions to manipulate the IP address space

'''

def add_IP4_Network(bid, cidr, props):
    URL = BaseURL + 'addIP4Network'

    params = {
        'blockId': bid,
        'CIDR': cidr,
        'properties': props
    }

    req = resquests.post(URL, headers=AuthHeader, params=params)
    return req.json()

'''

addEntity Description


addEntity() is a generic method for adding:
    Configurations,
    DNS zones, and
    DNS resource records.

When using addEntity() to add a zone, you must specify
a single zone name without any . (dot) characters.
The parent object must be either a DNS view or another DNS zone.

Output / Response
    Returns the object ID for the new Entity.

API call: long addEntity( long parentId, APIEntity entity )

Parameter Description
    parentId: The object ID of the parent DNS view or
              DNS zone to which the zone is added.
          
entity:  The zone name, without any . (dot) characters, to be added.

The entity has the following JSON structure:

 {'id': 2516291, 'name': 'org', 'type': 'Zone', 'properties': None}
 
 or when filled in:
 
 
'''

def add_entity(parent_id, entity):
    URL = BaseURL + 'addEntity'
    params = {'parentId': parent_id}

    req = requests.post(URL, headers=AuthHeader, params=params, json=entity)
    return req.json()


'''

Add Zone: Adds DNS zones.

When using addZone(), you can use . (dot) characters to create the top level domain
and subzones.

Output / Response

Returns the object ID for the new DNS zone.

API Call:
long addZone( long parentId, String absoluteName, String properties )


Parameter Description:


parentId: The object ID for the parent object to which the zone is being added.
          For top-level domains, the parent object is a DNS view.
          For sub zones, the parent object is a top-level domain or DNS zone.
          
absoluteName: The complete FQDN for the zone with no trailing dot
              (for example, frodo.org).
              
properties: Adds object properties, including a flag for deployment,
            an optional network template association, and
            user-defined fields in the format:
                deployable=<true|false>|template=<template id>|
                <userField>=<userFieldValue>
                
The deployable flag is false by default and is optional. To make the zone
deployable, set the deployable flag to true.

'''


def add_zone(fqdn):
    URL = BaseURL + 'addZone'

#    if is_zone(fqdn):
#        print fqdn, 'is already a zone and can not be added'
#        return -1

    if fqdn in LegalTLDs:
        parent_id = ViewId
    else:
        parent_id = get_id_by_name(parent_name(fqdn))
        info = get_entity_by_id(parent_id)
        if info['type'] != 'Zone':
            bam_error('The parent of', fqdn, 'is not a zone')
    
    params = {
            'parentId': parent_id,
            'absoluteName': fqdn,
            'properties': 'deployable=true',
    }

    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()


'''

Get Zones by Hint
    Returns an array of accessible zones of child objects for a given containerId value.

Output / Response
    Returns an array of zones based on the input argument without their properties fields populated, or returns
    an empty array if containerId is invalid. If no access right option is specified, the View access level will be
    used by default.

API Call:
    APIEntity[] getZonesByHint( long containerId, int start, int count, String options )

Parameters:
    containerId: The object ID for the container object. It can be the object ID of any object in
                 the parent object hierarchy. The highest parent object can be the configuration level.
    start:  Indicates where in the list of objects to start returning objects.
            The list begins at an index of 0.

    count:  Indicates the maximum number of child objects that this method will return.
            The maximum number of child objects cannot exceed more than 10.

    options:
    A string containing options. The Option names available in the ObjectProperties are:
        ObjectProperties.hint, ObjectProperties.accessRight, and ObjectProperties.overrideType.
        Multiple options can be separated by a | (pipe) character. For example:
            hint=ab|overrideType=HostRecord|accessRight=ADD
        The values for ObjectProperties.hint option can be the prefix of a zone name.  For example:
            String options = ObjectProperties.hint + "=abc|"
        The values for the ObjectProperties.accessRight and ObjectProperties.overrideType
        options must be one of the constants listed in Access Right Values on page 189
        and Object Types on page 209. For example:
            String options = ObjectProperties.accessRight + "=" + AccessRightValues.AddAccess +
                "|"+ ObjectProperties.overrideType + "=" + ObjectTypes.HostRecord;

'''

def get_zones_by_hint(containerid, options, start=0, count=1):
        URL = BaseURL + 'getZonesByHint'
        if count > 10:
            count = 10
        params = {
            'containerId': containerid,
            'start': start,
            'count': count,
            'options': options
        }
        req = requests.get(URL, headers=AuthHeader, params=params)
        return req.json()


'''

Add Zone Template
    Adds a DNS zone template.

Output / Response:
    Returns the object ID of the new DNS zone template.

API Call:
long addZoneTemplate( long parentId, String name, String properties )

Parameter Description:
    parentId: The object ID of the parent DNS view when adding a view-level zone
              template. The object ID of the configuration when adding
              a configurationlevel zone template.
    name: The name of the DNS zone template. This value can be an empty string ("").
    
    properties: Adds object properties, including user-defined fields.


'''


def add_zone_template(parent_id, name, properties):
    URL = BaseURL + 'addZoneTemplate'
    
    params = {
        'parentId': parent_id,
        'name': name,
        'properties': properties,
    }
    
    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()
    

'''

Adding Resource Records  Description

viewId: Object ID for the parent view

absoluteName: Fully Qualified Domain Name

type: One of
    AliasRecord
    HINFORecord
    HOSTRecord (see add_host_record)
    MXRecord
    TXTRecord

rdata: Data for the RR in the BIND format

'''

def add_resource_record(fqdn, typ, rrdata, ttl=86400, props='comments=EmTee|'):
    URL = BaseURL + 'addResourceRecord'
    params = {
        'viewId': ViewId,
        'absoluteName': fqdn,
        'type': typ,
        'rdata': rrdata,
        'ttl': str(ttl),
        'properties': props
    }
    if Debug:
        print(params)
    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()


'''

Host Records
A host record, or A record, designates an IP address for a device.
A new host requires a name and an IP address. Multiple addresses may exist
for the same device. Set the time-to-live for this record to an override value
here so that the record has a longer or shorter ttl. A comment field is also included.


Add Host Record
Adds host records for IPv4 or IPv6 addresses. All addresses must be valid addresses.
This method will add the record under a zone. In order to add records under templates,
you must use Add Entity for Resource Records on page 124.
When adding a host record, the reverseRecord property, if not explicitly set
in the properties string, is set to true and Address Manager creates
a reverse record automatically. IPv4 addresses can be added in both
workflow and non-workflow mode. IPv6 addresses can be added in non-workflow mode only.
For more information on workflow mode, see Workflow Change Requests on page 182.

Output / Response
Returns the object ID for the new host resource record.
API call:
long addHostRecord(long viewId, String absoluteName, String addresses,
                    long ttl, String properties)

Parameters:

    viewId: The object ID for the parent view to which this record is being added.
    
    absoluteName: The FQDN for the host record. If you are adding a record in a zone
                  that is linked to a incremental Naming Policy, a single hash (#)
                  sign must be added at the appropriate location
                  in the FQDN. Depending on the policy order value,
                  the location of the single hash (#) sign varies.

    addresses: A list of comma-separated IP addresses
                (for example, 10.0.0.5,130.4.5.2).
    
    ttl: The time-to-live value for the record.
         To ignore the ttl, set this value to -1.
         
    properties:  Adds object properties, including comments and user-defined fields.

'''


def add_host_record(fqdn, ips, ttl=86400, properties='comments=EmTee|'):
    URL = BaseURL + 'addHostRecord'

# adding to the top level of the zone requires a leading dot
    if is_zone(fqdn):
        fqdn = '.' + fqdn

    params = {
      'viewId': ViewId,
      'absoluteName': fqdn,
      'addresses': ips,
      'ttl': ttl,
      'properties': properties
    }
    if Debug:
        print('fqdn', fqdn)
        print('ips', ips)

    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()


'''

Add Bulk Host Records

Adds host records using auto-increment from the specific starting address.
This method will add the record under a zone. In order to add records under templates,
you must use Add Entity for Resource Records on page 124.
This method adds host records to a zone linked to a DNS naming policy,
each with an IP address autoincremented starting from a specific address in a network.

Output / Response
Returns an array of host record APIEntity objects based on available addresses and number of IP
addresses required. If no addresses are available, an error will be shown.
API call:
APIEntity[] addBulkHostRecord ( long viewId, String absoluteName, long ttl, long
networkId, String startAddress, int numberOfAddresses, String properties)

Parameter Description
viewId The object ID for the parent view to which this record is being added.
absoluteName The FQDN for the host record. If you are adding a record in a zone that is linked
to a incremental Naming Policy, a single hash (#) sign must be added at the
appropriate location in the FQDN. Depending on the policy order value, the
location of the single hash (#) sign varies.
ttl The time-to-live value for the record. To ignore the ttl, set this value to -1.
networkId The network which to get the available IP addresses. Each address is used for
one host record.
startAddress The starting IPv4 address for getting the available addresses.
numberOfAddresses The number of addresses.
properties excludeDHCPRange=true/false, if true then IP addresses within a DHCP
range will be skipped. This argument can also contain user-defined fields.


'''

'''

Get Host Record by Hint
    Returns an array of objects with host record type.

Output / Response
    Returns an array of host record APIEntity objects.

API call:
    APIEntity[] getHostRecordsByHint ( int start, int count, String options)

Parameters:

    start:  Indicates where in the list of objects to start returning objects.
            The list begins at an index of 0.
    count:  Indicates the maximum of child objects that this method will return.
            The value must be less than or equal to 10.

    options: A string containing options. The supported options are hint and retrieveFields.
        Multiple options can be separated by a | (pipe) character. For example:
            hint=^abc|retrieveFields=false
        If the hint option is not specified in the string, searching criteria will be based on
        the same as zone host record. The following wildcards are supported in the hint option.

        * ^—matches the beginning of a string. For example: ^ex matches example but not text.
        * $—matches the end of a string. For example: ple$ matches example but not please.
        * ^ $—matches the exact characters between the two wildcards. For example:
            ^example$ only matches example.
        * ?—matches any one character. For example: ex?t matches exit.
        * *—matches one or more characters within a string.
            For example: ex*t matches exit and excellent.

        The default value for the retrieveFields option is set to false. If the option is set
        to true, user-defined field will be returned. If the options string does not contain
        retrieveFields, user-defined field will not be returned.

'''

def get_host_records_by_hint(options, start=0, count=10):
    URL = BaseURL + 'getHostRecordsByHint'
    params = {
      'options': options,
      'start': start,
      'count': count,
    }
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()

# Editing specific types of Resource Records

'''

Add Text Records

    This method will add the record under a zone.

Output / Response:
    Returns the object ID for the new TXT record.

API call:
long addTXTRecord ( long viewId, String absoluteName, String txt, long ttl, String properties )
Parameter Description
viewId:
    The object ID for the parent view to which the record is being added.
absoluteName:
    The FQDN of the text record. If you are adding a record in a zone
    that is linked to a incremental Naming Policy, a single hash (#)
    sign must be added at the appropriate location in the FQDN. Depending
    on the policy order value, the location of the single hash (#) sign
    varies.

txt:
    The text data for the record.
ttl:
    The time-to-live value for the record. To ignore the ttl, set this value to -1.
properties:
    Adds object properties, including comments and user-defined fields.

'''

def add_TXT_Record(absname, txt, ttl=86400, props='comments=EmTee|'):
    URL = BaseURL + 'addTXTRecord'
    params = {
        'viewId': ViewId,
        'absoluteName': absname,
        'txt': txt,
        'ttl': ttl,
        'properties': props
    }
    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()

'''

Generic Records

Use the generic resource record methods to add and update the
following resource record types:
    A6, AAAA, AFSDB, APL, CAA, CERT, DNAME, DNSKEY, DS, ISDN, KEY,
    KX, LOC, MB, MG, MINFO, MR, NS, NSAP, PX, RP, RT, SINK, SSHFP,
    TLSA, WKS, and X25.
The fields available are:
    name, type (which defines the custom record type), and data
    (the rdata value for the custom type). The time-to-live for this
    record can be set to an override value, so the record has a longer
    or shorter ttl. A comment field is also included.

Output / Response
    Returns the object ID for the new generic resource record

'''

def add_Generic_Record(viewid, absname, rr_type, rr_data, ttl, props):
    URL = BaseURL + 'addGenericRecord'
    params = {
        'viewId': viewid,
        'absoluteName': absname,
        'type': rr_type,
        'rdata': rr_data,
        'ttl': ttl,
        'properties': props
    }
    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()

def add_MX_Record(absname, priority, mx_host, ttl=86400, props='comments=EmTee|'):
    URL = BaseURL + 'addMXRecord'
    params = {
        'viewId': ViewId,
        'absoluteName': absname,
        'priority': priority,
        'linkedRecordName': mx_host,
        'ttl': ttl,
        'properties': props
    }
    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()


def add_ExternalHost_Record(viewid, ex_host, props):
    URL = BaseURL + 'addExternalHostRecord'
    params = {
        'viewId': viewid,
        'name': ex_host,
        'properties': props
    }
    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()

'''

This method attempts to link to an existing host record. If an existing host record cannot be located, the
method attempts to link to an existing external host record. If neither can be located, the method fails. This
method will add the record under a zone`

Output / Response
    Returns the object ID for the new alias resource record.

API call:
long addAliasRecord (long viewId, String absoluteName, String linkedRecordName, long ttl, String properties )

Parameter Description
    viewId: The object ID for the parent view to which this record is being added.

    absoluteName: The FQDN of the alias.
        If you are adding a record in a zone that is linked to
        a incremental Naming Policy, a single hash (#) sign must be added at the
        appropriate location in the FQDN. Depending on the policy order value, the
        location of the single hash (#) sign varies.

    linkedRecordName: The name of the record to which this alias will link.

    ttl: The time-to-live value for the record. To ignore the ttl, set this value to -1.

    properties: Adds object properties, including comments and user-defined fields.
'''


def add_Alias_Record(absname, link, ttl=86400, props='comments=EmTee|'):
    URL = BaseURL + 'addAliasRecord'
    params = {
        'viewId': ViewId,
        'absoluteName': absname,
        'linkedRecordName': link,
        'ttl': ttl,
        'properties': props
    }
    req = requests.post(URL, headers=AuthHeader, params=params)
    return req.json()


def get_system_info():
    URL = BaseURL + 'getSystemInfo'
    req = requests.get(URL, headers=AuthHeader)
    code = req.status_code
    if req.status_code == 200:
        return req.json()
    else:
        bam_error(req.text)

def get_configuration_setting(id, name):
    URL = BaseURL + 'getConfigurationSetting'
    params = {'configurationId': id, 'settingName': name}
    req = requests.get(URL, headers=AuthHeader, params=params)
    return req.json()





'''

Higher Level Functions

'''

def bam_error(err_str):
    print('BAM error:', err_str)
    sys.exit()


# Takes a property list as a dictionary e.g.
# {'ttl': '86400', 'absoluteName': 'fwsm-tabu.bkup.utoronto.ca', 'addresses': '128.100.96.158', 'reverseRecord': 'true'}
# and returns it as a string equivalent:
#   ttl=86400|absoluteName=fwsm-tabu.bkup.utoronto.ca|addresses=128.100.96.158|reverseRecord=true|

def dict2props(d):
    props = []
    for k,v in d.items():
        props.append('='.join([k,v]))
    return '|'.join(props) + '|'


# Takes a property list as a string e.g.
#   ttl=86400|absoluteName=fwsm-tabu.bkup.utoronto.ca|addresses=128.100.96.158|reverseRecord=true|
# and returns it as a dictionary equivalent:
#   {'ttl': '86400', 'absoluteName': 'fwsm-tabu.bkup.utoronto.ca', 'addresses': '128.100.96.158', 'reverseRecord': 'true'}

def props2dict(str):
    dd = {}
    ll = str.split('|')
    for i in ll[0:-1]:
        kv = i.split('=')
        dd[kv[0]] = kv[1]
    return dd


def get_token():
    global BaseURL



'''
    text: "Session Token-> BAMAuthToken: 7NfY4MTU1NDM5MDU1MzkzMzppc2VhLWFwaQ== <- for User : test-api"
    json: Session Token-> BAMAuthToken: 7NfY4MTU1NDM5MDU1MzkzMzppc2VhLWFwaQ== <- for User : test-api
'''

def bam_init(debug):
    global Debug, AuthHeader, ConfigId, ViewId, BaseURL

#   ConfigName = 'Production'
    ConfigName = 'Test'
    ViewName = 'Public'
    RootId = 0

    BaseURL = os.getenv('BAM_API_URL')
    if BaseURL is None:
        bam_error('The BAM_API_URL shell variable must be set')
    env_name = os.getenv('BAM_USER')
    env_pw = os.getenv('BAM_PW')
    if env_name is None or env_pw is None:
        bam_error('The BAM_USER and BAM_PW shell variables must be set')

    Debug = debug
    Creds = {'username': env_name, 'password': env_pw}

    URL = BaseURL + 'login'
    req = requests.get(URL, params=Creds)
    if Debug:
        print('status code: {}'.format(req.status_code))
        print('headers: {}'.format(req.headers))
        print('text: {}'.format(req.text))
        print('json: {}'.format(req.json()))

    session_token = req.text.split()[3]

    AuthHeader = {
      'Authorization': 'BAMAuthToken: ' + session_token,
      'Content-Type': 'application/json'
    }

    if Debug:
        print('Authorization Header: {}'.format(AuthHeader))

    config_ent = get_entity_by_name(RootId, ConfigName, 'Configuration')
    if Debug:
        print('Config Entity: {}'.format(config_ent))
    ConfigId = config_ent['id']
    if ConfigId > 0:
        view_ent = get_entity_by_name(ConfigId, ViewName, 'View')
        if Debug:
            print('View Entity: {}'.format(view_ent))
        ViewId = view_ent['id']
    else:
        bam_error('Error: The parent (Configuration) Id must be set before setting the View Id')

    if Debug:
        val = get_system_info()
        vals = val.split('|')
        for val in vals:
            print(val)
        print()


def bam_logout():
    URL = BaseURL + 'logout'
    req = requests.get(URL, headers=AuthHeader)
    sys.exit()


# Deletes all data and RRs in the Zone tree including other Zones

def delete_zone(fqdn):
    zone_id = get_zone_id(fqdn)
    if zone_id:
        val = delete(zone_id)
        return val


#
# given andy.bozo.cathy.dan.ca it returns bozo.cathy.dan.ca
#

def parent_name(fqdn):
    return fqdn.split('.',1)[1]

#
# Get the information of an Entity (Id and parentId) given a FQDN or a CIDR block
# Quick and dirty technique, based only on the fqdn
#

def get_info_by_name(fqdn):
    obj_id = ViewId
    names = fqdn.split('.')
    lg = len(names)
    for name in names[::-1]:
        ent = get_entity_by_name(obj_id, name, 'Entity')
        if Debug:
            print('name: {} entity: {}'.format(name, ent))
        pid = obj_id
        obj_id = ent['id']
    ent['pid'] = pid
    if ent['type'] == 'Zone':
        pid = ent['id']
        name = ''
    else:
        pid = ent['pid']
        name = fqdn.split('.')[0]
    for obj_type in RRObjectTypes:
        ents = get_entities(pid, obj_type, 0, 50)
        if Debug:
            if type(ents) is str:
                print('Type: {} Ent: {}'.format(obj_type, ents))
            else:
                for e in ents:
                    if e['name'] == name:
                        print('Type: {} Ent: {}'.format(obj_type, e))
    return ent


def view_info_by_name(fqdn, *argv):
    is_Zone = False
    ll = len(argv)
    if Debug: 
        print('fqdn: {}'.format(fqdn))
        for arg in argv:
            print('arg: {}'.format(arg))
    if ll > 0:
        rr_type = argv[0]
        obj_rr_type = RRTypeMap[rr_type]['obj_type']
        if ll > 1:
            obj_rr_key = RRTypeMap[rr_type]['prop_key']
            value = argv[1]
    else:
        obj_rr_type = 'Entity'

    obj_id = ViewId
    names = fqdn.split('.')
    for name in names[::-1]:
        ent = get_entity_by_name(obj_id, name, 'Entity')
        if Debug:
            print('name: {} entity: {}'.format(name, ent))
        pid = obj_id
        obj_id = ent['id']
    ent['pid'] = pid
    if ent['type'] == 'Zone':
        is_Zone = True
        pid = ent['id']
        name = ''
    else:
        name = names[0]
    if Debug:
        print()
    if ll == 0:
        ids = []
        for obj_type in RRObjectTypes:
            ents = get_entities(pid, obj_type, 0, 50)
            for e in ents:
                if e['name'] == name:
                    ids.append(e['id'])
        bind_print(ids)
        if is_Zone:
            rrs = {}
            for obj_type in RRObjectTypes:
                ents = get_entities(pid, obj_type, 0, 50)
                if len(ents):
                    for e in ents:
                        name = e['name']
                        if len(name):
                            if name in rrs:
                                lst = rrs[name]
                                lst.append(e)
                                rrs[name] = lst
                            else:
                                rrs[name] = [e]

            ids = []
            for fqdn in sorted(rrs):
                for e in rrs[fqdn]:
                    ids.append(e['id'])
            bind_print(ids)

    elif ll > 0:
        ents = get_entities(pid, obj_rr_type, 0, 50)
        ids = []
        for e in ents:
            if e['name'] == name:
                if ll == 1:
                    ids.append(e['id'])
                else:
                    d = props2dict(e['properties'])
                    if value in d[obj_rr_key]:
                        ids.append(e['id'])
    return ent

'''

 Find a RR based on more or less specificity by matching:
 a. fqdn
 b. fqdn + RRtype
 c. fqdn + RRtype + value

 Return an list of matching entities. If there are no matches, return an empty lists


'''


def find_rr(fqdn, *argv):
    obj_types = RRObjectTypes

    arglen = len(argv)
    if arglen > 0:
        rr_type = argv[0]
        obj_types = [RRTypeMap[rr_type]['obj_type']]
        if arglen > 1:
            value = argv[1]
            obj_rr_key = RRTypeMap[rr_type]['prop_key']

    if fqdn[-1] == '.':
        trailing_dot = True
        fqdn = fqdn[:-1]
    else:
        trailing_dot = False

    names = fqdn.split('.')
    tld = names.pop()
    if tld not in LegalTLDs:
        print('Top level domain name must be one of: {}'.format(LegalTLDs))
    ent = get_entity_by_name(ViewId, tld, 'Entity')
    par_id = ent['id']

    for name in names[::-1]:
        ent = get_entity_by_name(par_id, name, 'Entity')
        ent['pid'] = par_id
        par_id = ent['id']
    obj_id = ent['id']
    par_id = ent['pid']
    rr_ents = []
    if ent['type'] == 'Zone':
        par_id = obj_id
        name = ''
        for obj_type in obj_types:
            ents = get_entities(par_id, obj_type, 0, 100)
            if len(ents):
                if trailing_dot:
                        rr_ents += ents
                else:
                    for ent in ents:
                        if ent['name'] == name:
                            rr_ents.append(ent)
    else:
        for obj_type in obj_types:
            ents = get_entities_by_name(par_id, name, obj_type, 0, 10)
            if len(ents):
                rr_ents += ents

    if arglen == 2 and rr_type != 'CNAME':
        found = False
        if rr_type == 'A' or rr_type == 'TXT' or rr_type == 'MX':
            for ent in rr_ents:
                d = props2dict(ent['properties'])
                values = d[obj_rr_key]
                if rr_type == 'A':
                    current_ips = values.split(',')
                    if value in current_ips:
                        found = True
                        rr_ents = [ent]
                        break
                elif rr_type == 'MX':
                    (priority, mxhost) = value.split(',')
                    if d['priority'] == priority and mxhost == values:
                        found = True
                        rr_ents = [ent]
                        break
                elif value == values:
                    found = True
                    rr_ents = [ent]
                    break
        if not found:
            rr_ents = []

    ids = []
    for rr_ent in rr_ents:
        if rr_ent['name'] == '':
            ids.append(rr_ent['id'])
    for rr_ent in rr_ents:
        if rr_ent['name'] != '':
            ids.append(rr_ent['id'])
    return ids

def view_rr(fqdn, *argv):
    ids = find_rr(fqdn, *argv)
    bind_print(ids)

#
# Print out a list of BAM RR Entity IDs in Bind format
#

def bind_print(ent_ids):
    if len(ent_ids) == 0:
        print('No RRs to display')
        return
    str_lens = []
    for ent_id in ent_ids:
        ent = get_entity_by_id(ent_id)
        d = props2dict(ent['properties'])
        fqdn = d['absoluteName']
        str_lens.append(len(fqdn))
    maxlen = max(str_lens)
    fmt_str = '{:<' + str(maxlen+4) + '} IN {:>5} {:<6} {}'
    mx_str = fmt_str + ' {}'
    for ent_id in ent_ids:
        ent = get_entity_by_id(ent_id)
        d = props2dict(ent['properties'])
        fqdn = d['absoluteName']
        if 'ttl' in d.keys():
            ttl = d['ttl']
        else:
            ttl = d['ttl'] = '86400'
            ent['properties'] = dict2props(d)
            update(ent)
        if ttl == '86400':
            ttl = '     '
        rr_type = BAM2Bind[ent['type']]
        value = d[RRTypeMap[rr_type]['prop_key']]
        if rr_type == 'A':
            values = value.split(',')
            for val in values:
                print(fmt_str.format(fqdn, ttl, rr_type, val))
        elif rr_type == 'TXT':
            print(fmt_str.format(fqdn, ttl, rr_type, value))
        elif rr_type == 'MX':
            pri = d['priority']
            print(mx_str.format(fqdn, ttl, rr_type, pri, value))
        else:
            print(fmt_str.format(fqdn, ttl, rr_type, value))

#
# A similar function but checking both the rr_type and value
# returns 0 if object can not be found
#

def object_find(fqdn, rr_type, value):
    id = 0
    if rr_type == 'MX':
        (priority, value) = value.split(' ')

    obj_type = RRTypeMap[rr_type]['obj_type']
    prop_key = RRTypeMap[rr_type]['prop_key']

    names = fqdn.split('.')
    tld = names.pop()
    tld_ent = get_entity_by_name(ViewId, tld, 'Zone')
    pid = tld_ent['id']
    pname = tld
    while (len(names)):
        name = names.pop()
        ent = get_entity_by_name(pid, name, 'Entity')
        obj_id = ent['id']
        obj_ent = get_entity_by_id(obj_id)
        if Debug:
            print('name, id, ent:', name, obj_id, ent)
        if len(names) == 0 and obj_id:
            obj_type = obj_ent['type']
            if obj_type == 'Zone':
                pid = obj_id
            else:
                ents = get_entities(pid, obj_type, 0, 100)
                if len(ents):
                    for ent in ents:
                        if 'properties' in ent and ent['properties'] is not None:
                            d = props2dict(ent['properties'])
                            if d['absoluteName'] == fqdn:
                                if 'addresses' in d:
                                    obj_id = ent['id']
                                elif value == d[prop_key]:
                                    obj_id = ent['id']
        pname = name
        pid = obj_id
    return obj_id


def get_id_by_name(fqdn):
    ent = get_info_by_name(fqdn)
    return ent['id']


def get_pid_by_id(id):
    ent = get_parent(id)
    return ent['id']


def get_info_by_id(id):
    ent = get_entity_by_id(id)
    pid = get_pid_by_id(id)
    ent['pid'] = pid
    return ent


#
# return the parent ID of an Object based on its name
#


def get_pid_by_name(fqdn):
    info = get_info_by_name(fqdn)
    return info['pid']

#
# gets an entity based on fqdn
#

def get_host_info(vid, fqdn):
    names = fqdn.split('.')
    lg = len(names)
    igd = vid
    for name in names[::-1]:
        ent = get_entity_by_name(id, name, 'Entity')
        if ent['type'] == 'Zone':
            id = ent['id']
            print(names[:l])
            lg -= 1
        else:
            break
    name = '.'.join(names[:l])
    ent = get_entity_by_name(id, name, 'GenericRecord')
    return ent
    
#
# retrieves the Id of a Zone or Subzone
#

def get_zone_id(fqdn):
    info = get_info_by_name(fqdn)
    if info['type'] == 'Zone':
        return info['id']
    else:
        print(fqdn, 'is not a zone')

#
# is_zone takes a name/fqdn as input and returns: False
# if it is not a zone, otherwise the object_Id of the zone
#

def is_zone(fqdn):
    ent = get_info_by_name(fqdn)
    if ent['type'] == 'Zone':
        return ent['id']
    else:
        return False

#
# Add a zone using the generic add_generic call rather than
# the specific add_zone()one
#
    
def add_zone_generic(fqdn):
    dot = '.'
    n = fqdn.split(dot)
    nm = n[0]
    subzone = dot.join(n[1:])
    par_id = get_id_by_name(subzone)
    props = 'deployable=true|'
    props += 'absoluteName=' + fqdn + '|'
    ent = {
        'name': nm,
        'type': 'Zone',
        'properties': props
    }
    val = add_entity(par_id, ent)
    return val

def is_external_host(fqdn):
    if fqdn in get_external_hosts():
        return True
    else:
        return False


def is_host_record(fqdn):
    ent = get_info_by_name(fqdn)
    if Debug:
        print('host record check: {}'.format(ent))
    if ent['id'] > 0 and ent['type'] == 'HostRecord':
        return True
    else:
        return False


def add_PTR_rr(fqdn, ipaddr, ttl=86400):
    macaddr = ''
    hostinfo = ''
    action = 'MAKE_STATIC'
    props = 'ptrs=' + str(ViewId) + ',' + fqdn
    val = assign_IP4_Address(ConfigId, ipaddr, macaddr, hostinfo, action, props)
    return val

def get_external_hosts():
    exhosts = []
    ents = get_entities(ViewId, 'ExternalHostRecord', 0, 250)
    for ent in ents:
        exhosts.append(ent['name'])
    return exhosts

def add_external_host(exhost):
    exhosts = get_external_hosts()
    if exhost not in exhosts:
        val = add_ExternalHost_Record(ViewId, exhost, 'comments=Ext. Host|')
        print(val)

#
# delete a given generic RR
#

def delete_rr(fqdn, rr_type, *argv):
    if argv:
        value = argv[0]
    else:
        value = '*'
    if Debug:
        print('Input data: {} {} {} {}'.format(fqdn, rr_type, value))

# there can only be one CNAME record for a FQDN so the value does not matter
    if rr_type == 'CNAME':
        obj_id = find_rr(fqdn, rr_type)
    else:
        obj_id = find_rr(fqdn, rr_type, value)
    if obj_id:
        print('This RR exists and will be deleted')
        bind_print(obj_id)
        if rr_type == 'A':
            obj_prop_key = RRTypeMap[rr_type]['prop_key']
            ent = get_entity_by_id(obj_id[0])
            d = props2dict(ent['properties'])
            ip_list = d[obj_prop_key].split(',')
            ip_list.remove(value)
            if ip_list:
                d[obj_prop_key] = ','.join(ip_list)
                ent['properties'] = dict2props(d)
                update(ent)
            else:
                delete(obj_id[0])
        else:
            delete(obj_id[0])
    else:
        print('No RR exists matching {} {} {}'.format(fqdn,rr_type,value))


"""

Old delete routine

def delete_rr_old(fqdn, *argv):
    ll = len(argv)
    if ll:
        rr_type = argv[0]
# there should be only zero or one CNAME record per fqdn
        if rr_type == 'CNAME':
            id_list = find_rr(fqdn, rr_type)
            if len(id_list):
                obj_id = id_list[0]
                print('deleting:')
                bind_print([obj_id])
                delete(obj_id)
            else:
                print('No RR record of type {} associated with {}'.format(rr_type, fqdn))
        elif ll > 1:
            value = argv[1]
            obj_prop_key = RRTypeMap[rr_type]['prop_key']
            id_list = find_rr(fqdn, rr_type, value)
            if id_list:
                obj_id = id_list[0]
                if rr_type == 'A':
                    ent = get_entity_by_id(obj_id)
                    d = props2dict(ent['properties'])
                    ips = d[obj_prop_key].split(',')
                    ips.remove(value)
                    if ips:
                        d[obj_prop_key] = ','.join(ips)
                        ent['properties'] = dict2props(d)
                        print('Removing IP address: {} from RR(s):'.format(value))
                        update(ent)
                        bind_print([obj_id])
                    else:
                        print('Removing RR {} with IP address: {}'.format(fqdn, value))
                        delete(obj_id)
                        bind_print([obj_id])
                elif rr_type == 'TXT' or rr_type == 'CNAME' or rr_type == 'MX':
                    print('Removing {} record'.format(rr_type))
                    bind_print([obj_id])
                    delete(obj_id)
            else:
                print('Could not find RR with name {} of type {} with value {} to delete'.format(fqdn, rr_type, value))

"""


#
# fqdn is at the zone level or is a new RR below a zone
# new code using find_rr
#

def add_rr(fqdn, rr_type, value, ttl):
    if Debug:
        print('Input data: {} {} {} {}'.format(fqdn, rr_type, value, ttl))


    obj_prop_key = RRTypeMap[rr_type]['prop_key']
    obj_id = find_rr(fqdn, rr_type, value)
    if obj_id:
        print('This {} Record already exists'.format(rr_type))
        bind_print(obj_id)
    elif rr_type == 'A':
        obj_id = find_rr(fqdn, rr_type)
        if obj_id:
            ent = get_entity_by_id(obj_id[0])
            d = props2dict(ent['properties'])
            ip_list = d[obj_prop_key]
            ip_list += ',' + value
            d[obj_prop_key] = ip_list
            d['ttl'] = ttl
            ent['properties'] = dict2props(d)
            update(ent)
            bind_print(obj_id)
        else:
            obj_id = add_host_record(fqdn, value, ttl)
            print('Added the new Host Record')
            bind_print([obj_id])
    elif rr_type == 'TXT':
        obj_id = add_TXT_Record(fqdn, value, ttl)
        print('added new TXT record:')
        bind_print([obj_id])
    elif rr_type == 'CNAME':
        obj_id = add_Alias_Record(fqdn, value, ttl)
        print('added new CNAME record:')
        bind_print([obj_id])
    elif rr_type == 'MX':
        (priority, mx_host) = value.split(',')
        if is_zone(fqdn):
            fqdn = '.' + fqdn
        obj_id = add_MX_Record(fqdn, priority, mx_host, ttl)
        print('added new MX record:')
        bind_print([obj_id])
    return obj_id

"""
# old code

    obj_rr_type = RRTypeMap[rr_type]['obj_type']
    obj_prop_key = RRTypeMap[rr_type]['prop_key']
    name = fqdn.split('.')[0]

#
# use BAM higher level functions rather than lower level add_entity
#

    generic_ent = get_info_by_name(fqdn)
    obj_id = generic_ent['id']
    obj_type = generic_ent['type']
    obj_pid = generic_ent['pid']
    specific_ent = get_entity_by_id(obj_id)
    if Debug:
        print('generic entity:', generic_ent)
        print('specific entity:',specific_ent)
    is_Zone = False
    if obj_type == 'Zone':
        obj_pid = obj_id
        is_Zone = True
        name = ''
        fqdn = '.' + fqdn
    if obj_id:
        ents = get_entities(obj_pid, obj_rr_type, 0, 100)
        if Debug:
            for ent in ents:
                print('\t', ent)

#
# assumes that the value includes only ONE new IP address
#

    if rr_type == 'A':
        ip = value
        if obj_id: # if there were some RRs found
            obj = get_ipranged_by_ip(ip)
            if type(obj) is str or obj['id'] == 0:
                print('The IP Address {} is not in a defined network space'.format(ip))
                return False
            for ent in ents:
                if name == ent['name']:
                    if Debug:
                        print('update before: {}'.format(ent))
                    d = props2dict(ent['properties'])
                    old_ips = d[obj_prop_key].split(',')
                    if ip in old_ips:
                        print('IP address {} is already assigned to {}'.format(ip, fqdn))
                        return False
                    d[obj_prop_key] += ',' + ip
                    d['ttl'] = ttl
                    ent['properties'] = dict2props(d)
                    if Debug:
                        print('update after: {}'.format(ent))
                    update(ent)
                    if is_Zone:
                        fqdn = fqdn[1:]
                    print('Added an additional Host Record: {} <--> {}'.format(fqdn, ip))
                    break
            if obj_id: # no resource record matches found in the list of ents
                if Debug:
                    print('Adding a new Resource Record {}'.format(specific_ent))
                obj_id = add_host_record(fqdn, ip, ttl)
                if is_Zone:
                    fqdn = fqdn[1:]
                print('Added a new Host record: {} <--> {}'.format(fqdn, ip))
        else:   # no resource records of all of rr_type at zone or sub-zone level
            if Debug:
                print('Adding a First Resource Record of type: {}'.format(obj_rr_type))
            obj_id = add_host_record(fqdn, ip, ttl)
            if is_Zone:
                fqdn = fqdn[1:]
            print('Added a new Host record: {} <--> {}'.format(fqdn, ip))

    elif rr_type == 'TXT':
        if obj_id:
            updated = False
            duplicate = False
            for ent in ents:
                d = props2dict(ent['properties'])
                if name == ent['name'] and value == d[obj_prop_key]:
                    duplicate = True
                    if ttl != d['ttl']:
                        d['ttl'] = ttl
                        ent['properties'] = dict2props(d)
                        update(ent)
                        updated = True
                    break
            if updated:
                print('TXT record TTL updated:')
            elif duplicate:
                print('Duplicate of existing TXT record:')
            else:
                obj_id = add_TXT_Record(fqdn, value, ttl)
                print('added new TXT record:')
                bind_print([obj_id])
        else: # No TXT records at all
            obj_id = add_TXT_Record(fqdn, value, ttl)
            print('added new TXT record:')
            bind_print([obj_id])
        return obj_id

    elif rr_type == 'MX':
        (priority, mx_host) = value.split(',')
        if not (is_host_record(mx_host) or is_external_host(mx_host)):
                print('MX host:', mx_host, 'must be defined either as a Host Record or an External Host')
                return 0
        ent_id = 0
        if obj_id:
            change = True
            for ent in ents:
                props = ent['properties']
                d = props2dict(props)
                if name == ent['name']:
                    if mx_host == d[obj_prop_key]:
                        if priority == d['priority']:
                            if ttl == d['ttl']:
                                change = False
                                break
            if change:
                ent_id = add_MX_Record(fqdn, priority, mx_host, ttl)
                if type(ent_id) is str: 
                    print(ent_id)
                else:
                    print('Added the following RR:')
                    bind_print([ent_id])
            else:
                print('Duplicate MX Record')
        else:
            ent_id = add_MX_Record(fqdn, priority, mx_host, ttl)
            if type(ent_id) is str: 
                print(ent_id)
            else:
                print('Added the following RR:')
                bind_print([ent_id])
        return ent_id

    elif rr_type == 'CNAME':
        if not (is_host_record(value) or is_external_host(value)):
                print('Alias host:', value, 'must be defined either as a Host Record or an External Host')
                return 0
        ent_id = 0
        if is_Zone:
            print('CNAME records are not allowed at the top of a Zone')
            return 0
        if obj_id:
            cname_exists = False
            for ent in ents:
                if name == ent['name']:
                    print('A CNAME record already exists')
                    d = props2dict(ent['properties'])
                    if ttl != d['ttl'] or d[obj_prop_key] != value:
                        print('Updating it with the given data')
                        d[obj_prop_key] = value
                        d['ttl'] = ttl
                        ent['properties'] = dict2props(d)
                        update(ent)
                    cname_exists = True
                    break
            if not cname_exists:
                obj_id = add_Alias_Record(fqdn, value, ttl)
                print('Added CNAME record:')
                bind_print([obj_id])
        else:
            obj_id = add_Alias_Record(fqdn, value, ttl)
            print('Added CNAME record:')
            bind_print([obj_id])
        return obj_id

"""

#
# update a given RR to the state of the values given
# Using find_rr
#

def update_rr(fqdn, rr_type, value, ttl):

    id_list = find_rr(fqdn, rr_type)
    if not id_list:
        print('Can not find a RR to update with name {} with type {}'.format(fqdn, rr_type))
        return
# There should only be one RR found with the fqdb and type given and value
# If there are more than one, update the first one only
    obj_id = id_list[0]
    ent = get_entity_by_id(obj_id)
    if Debug:
        print('fqdn {} rr_type {} value {}'.format(fqdn, rr_type, value))
        print('ent bef', ent)
    prop_key = RRTypeMap[rr_type]['prop_key']
    d = props2dict(ent['properties'])
    d['ttl'] = ttl
    if rr_type ==  'MX':
        (pri, mx) = value.split(',')
        d[prop_key] = mx
        d['priority'] = pri
        ent['properties'] = dict2props(d)
    elif rr_type == 'A':
        org_value = value
        ip_list = value.split(',')
        ip_tup = tuple(ip_list)
        for ip in ip_tup:
            ip_test_ent = get_ipranged_by_ip(ip)
            if type(ip_test_ent) is str or ip_test_ent['id'] == 0:
                print('IP address: {} is not in a defined network'.format(ip))
                ip_list.remove(ip)
        if ip_list:
            d[prop_key] = ','.join(ip_list)
            ent['properties'] = dict2props(d)
        else:
            print('None of the IP addresses in {} could be updated'.format(org_value))
            return
    elif rr_type == 'TXT' or rr_type == 'CNAME':
        d[prop_key] = value
        ent['properties'] = dict2props(d)
    if Debug:
        print('ent aft:', ent)
    update(ent)
    print('Updated RR as follows:')
    bind_print([obj_id])
