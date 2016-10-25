About
----------
This document describes the expected keys and values in the various XML property list configuration files used by the Munki Enrollment Server.

Configuration Files
----------
### MES Main Configuration ###
* Path: **<container>/mes_virtualenv/mes/configuration.plist**
* Keys:
* **Site**: dictionary with your site information:
   * **organization_name**: string: A human-friendly name for your organization
   * **sub_organization_name**: string: A human-friendly name for your organization's IT group or division
   * **organization_prefix**: string: Reverse DNS name for your organization (for example, _org.something_)
* **ClientMunkiPrefs**: dictionary with metadata for the Apple Config Profile that the MES builds and delivers for configuring the Munki Client
   * **organization_prefix**: string: Reverse DNS name for your organization (for example, _org.something_)
   * **munki_mcx_defaults_domain**: string: Should be _ManagedInstalls_ unless the config file for the Munki client is moved.  This corresponds to _/Library/Preferences/ManagedInstalls.plist_.
   * **munki_mcx_payload_display_name**: string: The display name for the managed prefs payload included in the Apple Config Profile