# anzlic-validator QGIS Plugin

## Installation

* Install the plugin into your qgis plugin directory, 
along with other required elements listed in 
[ReadMe](README.md).

* Open the config directory and make sure that the required elements 
are listed in the config section. There are instructions listed in the
 header of the yaml config files and below [Config](## Config).

* Open the plugin through the plugin menu in QGIS.

## Guide

### Home
Once open the Home screen has two main options:

* **Create New Metadata** (Based on either an existing metadata file/ 
LINZ Template or another template)

	* The default button will select in the default LINZ template.
	
* **Edit Metadata** (Either by selecting an existing layer on the LDS 
to update the metadata or select an existing local metadata file.)
	
	* Refresh will update the list of layers/tables from the LDS. 
	Otherwise this will be updated whenever the plugin is reloaded in 
	QGIS or on opening of QGIS. 
	
Also on the home screen is **Settings**. In settings the configuration 
file can be updated. The default location for downloading XML Metadata 
files from the LDS, can be changed. Along with the option to remove all 
previously downloaded files.

### Layer Information

Basic Layer Information Can be entered Here:

* Hierarchy Level

* Title

* Alternate Title

* Abstract 
	
	* The **Bold**, *italic* and Link Buttons can be used on text in the
	 Abstract text box to easily add in as is seen in the LDS About 
	 Section.

* Purpose

### Contact Information

Both Metadata and Resource Contact Details can be added here:

* Individual/Organisation/Position Name
	
* Delivery Address
	
* City
	
* Postal Code

* Country
	
* Telephone & Facsimile
	
* Contact Role

There are buttons to auto fill one set of contact details into the other
 to provide a simple option.

***Note:***  if using the auto fill buttons the Contact Role should be 
different between Metadata & Resource Contact.

### Identification

Identification Information is across two tabs with the following:

* Resource History
	
* Resource Status
* Resource Maintenance & Date of Next Update
	
* Resource Reference System
	
	* The drop down option will give recently used reference systems in 
	QGIS, while Reference System Button will give the full selection 
	options. 
		
	* If the layer is entered using the Layer ID/ Name the reference 
	system will be double checked against the LDS in error-validation 
	checks.
* Resource Scale
	
	* Scale - Default QGIS Scale options are listed, however others can 
	be added.
		
	* Resolution - If a resolution is added, both the Value and the 
	Units of Measure need to be included.
		
	* If neither Scale or Resolution are wanted, make sure to uncheck 
	the main scale checkbox.
	
* Resource Key Dates
	
* Resource Topic Categories and Keywords

### Extent Information
Extent Information includes:

* Geographic Bounding Box
	
	* Load From Layer can be clicked, which will load the extent from 
	the current selected QGIS Layer.
		
* Geographic Description
	
* Temporal Information

### Legal & Security Information
Legal and Security Information includes:

* Resource & Metadata Security Classifications
	
* Resource & Metadata Use Copyright/ License Details.
	
* Default Resource & Metadata Use Copyright/ License Fields 
automatically be filled in using the **Fill Default** button, 
these are defined in the selected config file.

### Summary
The summary tab initially is empty, once the **Validate-Error Check** 
Button is clicked the Raw XML and Formated Metadata Tabs will populate. 

The formatted XML extracts the fields from the Raw XML for easier 
viewing. 

The abstract section will update to reflect any bold, italic, links as 
input so the correct formatting for the LDS can be seen.

### Error Check & Validation
When **Validate-Error Check** is clicked, each of the fields will be 
checked that they don't contain errors as defined in the config fields. 
Alongside validation against the ISO Schemas.

If an error is found due to the Error Check part of the Checks:

* The **Validation Log** Will display the details of the error, along 
with valid fields when necessary.	

*  A **Fix Error** button will display this will take you to the 
location of the error, displayed with a red __*__. Once the error is
fixed and the Validation Button is clicked again the Error Checker will 
continue through the rest of the document.

### Metadata Creation
Once all Validation and Error Checks have been completed, the **Create 
Metadata** Button will become clickable. 

This will create a local copy of the Metadata in the selected location 
at the beginning.

### Metadata Publication
Once Checks and Creation of the Metadata has occured the **Publish** 
Button will become available.

This will open a new Publish Dialog, from there if the Metadata was 
input directly from the LDS the Layer should already be selected. 
If not select the Layer to update and click Enter. 

Once Entered, there is a confirmation before the Metadata is published 
to the LDS.

On publish any errors will be written back to the Validation Log in the 
main ANZLIC Metadata Window.

## Config

Yaml configuration files are stored in the config directory of the 
anzlic-validator. 

Valid fields are listed below as well as valid options for those fields. 
If Invalid fields are entered the error-checker will not run and produce
an error listing which is the incorrect field.

Fields:

* Address (1- Metadata Contact, 2 - Resource Point of Contact)
Cannot use the 'CONTAINS' option as these are used for restricting 
selectable fields in the contact fields.
	* *INDIVIDUALNAME1*
	* *INDIVIDUALNAME2*
	* *ORGANISATIONNAME1*
	* *ORGANISATIONNAME2*
	* *POSITIONNAME1*
	* *POSITIONNAME2*
	* *VOICE1*
	* *VOICE2*
	* *FACSIMILE1*
	* *FACSIMILE2*
	* *DELIVERYADDRESS1*
	* *DELIVERYADDRESS2*
	* *CITY1*
	* *CITY2*
	* *COUNTRY1*
	* *COUNTRY2*
	* *POSTALCODE1*
	* *POSTALCODE2*
	* *EMAIL1*
	* *EMAIL2*
	* *ROLE1*
	* *ROLE2*

* Hierarchy Level. These should all contain the same value. 
	* *HIERARCHYLEVEL*
	* *HIERARCHYLEVELNAME*
	* *SCOPELEVEL*
	* *SCOPELEVELDESC*
	
* Security & Legal (Cannot use 'CONTAINS' for RESTRICCODERES & 
RESTRICCODEMET). All items inside RESTRICCODERES & RESTRICCODEMET will 
be checked for not just one or the other.
	* *SECURITYCLASSRES*
	* *SECURITYCLASSMET*
	* *RESTRICCODERES*
	* *RESTRICCODEMET*
	* *RESOURCECON*
	* *METADATACON*
	
* Extent
	* *EXTENTDESCRIPTION*
	* *EXTENTBOUNDINGBOX*
	* *EXTENTTEMPORAL*

* Resource Identification Details. 

	* Cannot have both SCALE and RESOLUTION
	set to TRUE/Values.
		* *SCALE*
		* *RESOLUTION*
	* 1 is checking not None/Empty, while 2 is checking against the LDS 
	to confirm reference system is correct.
		* *REFERENCESYS1*
		* *REFERENCESYS2*
	* *TITLE*
	* *ALTTITLE*
	* *PURPOSE*
	* *STATUS*
	* *LINEAGE*
	* *LINKAGE*
	* *SPATIALREPRESENTATION*
	* *TOPICCATEGORY*
	* *FID*
	* *MAINTENANCE*
	* *MAINTNEXTUPDATE*
	* *KEYWORD*
	* All Items will be checked for.
		* *KEYDATE*

* Format - Only TRUE/False values.
	* *DATEFORMAT*
	* *EMPTYFORMAT*

Additional fields below can be used to set default values for copyright 
& license information:

* *RCOPYRIGHT*
* *MCOPYRIGHT*
* *RLICENSE*
* *MLICENSE*

--------------------------

To check if a field exists and is not none or empty use. 

* *NAME: True*. Else Use *NAME: False*

	Ie. INDIVIDUALNAME: True


To check if a field is a particular field use the field in quotes. 

* *NAME: "MUST BE THIS"*

	Ie.  INDIVIDUALNAME: "Omit"

To check if a field is in a range of values use the same as a single 
field inside brackets. 
	
* *NAME: ["this", "or", "this"]*
	
	Ie. INDIVIDUALNAME: ["omit", "Omit"]

To check if a field exists or is in a range of values ONLY if it exists 
add "NONE" to check if not inside the brackets.

* *NAME: ["this", "NONE"]*

	Ie. INDIVIDUALNAME: ["omit", "NONE"]
	
	Adding "EMPTY" will also ignore if there are empty tags existing. 

To check if particular text(s)  is included in fields, this can be done 
by inclosing the fields in '[]' and adding the text 'CONTAINS' like so:

* RESOURCECON: [True, ['CONTAINS','CC BY 4.0']] *or*

* RESOURCECON: [True, ['CONTAINS','CC BY 4.0', 'LINZ']]

* Where the True/False element remains as previous, but ['CONTAINS', ...]
is added, where any number of fields may be added to be checked that they
exist.

