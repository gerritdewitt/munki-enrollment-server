#!/usr/bin/env python

# enrollment.py
# Munki Enrollment Server
# Collection of Python methods used by the Enrollment Server.

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# Project started 2015-06-15.  This file created 2015-07-23.
# 2016-09-19.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.
# References: See top level Read Me.

import os, base64, uuid, plistlib, xml, tarfile
from cStringIO import StringIO
# Load our modules:
import common
import devices
import manifests
import security
# Import configuration:
import configuration_classes as config
config_app = config.ServerApp()
config_munki_client = config.ClientMunkiPrefs()

def do_enrollment(given_serial):
    '''Abstracted method covering the enrollment procedure.
        Returns tar file contents or None.'''
    # Validate serial:
    given_serial = devices.validate_serial_number(given_serial)
    if not given_serial:
        common.logging_error("Serial number failed validation.")
        return None
    # Generate manifest:
    manifests.make_computer_manifest(given_serial)
    # Create private key:
    client_key = security.generate_private_key()
    # Create CSR:
    client_csr = security.generate_csr(client_key,given_serial)
    # Read CA certificate:
    ca_cert = security.read_ca_cert()
    ca_cert_p12_data = security.make_p12_with_ca_cert(ca_cert,given_serial)
    ca_cert_cn = security.read_cert_cn(ca_cert)
    # Sign CSR:
    client_cert = security.sign_with_ca(client_csr,ca_cert)
    # Generate mobileconfig:
    mobileconfig_contents = make_mobileconfig(given_serial,ca_cert_p12_data,ca_cert_cn)
    if not mobileconfig_contents:
        common.logging_error("Failed to generate mobileconfig_contents.")
        return None
    # Generate identity PEM (client key + client cert + CA cert):
    pki_contents = security.make_identity_pem_string(client_key,client_cert,ca_cert)
    if not pki_contents:
        common.logging_error("Failed to generate pki_contents.")
        return None
    # Return tar file:
    return make_tar_file(given_serial,pki_contents,mobileconfig_contents)

def make_tar_file(given_serial,given_pki_contents,given_mobileconfig_contents):
    '''Creates a tarfile with the configuration profile and client identity.
        Returns base64-encoded data representing the tarfile contents or
        None if something went wrong.'''
    common.logging_info("Generating tar file response for %s." % given_serial)

    tar_file_name = "mes-%s.tar" % given_serial.upper()
    tar_file_path = os.path.join(config_app.TEMP_DIR,tar_file_name)

    # Remove existing archive:
    if os.path.exists(tar_file_path):
        os.remove(tar_file_path)
        common.logging_info("Removed existing temp file: %s." % tar_file_path)

    # Create file objects:
    member_files_array = []
    # Config profile:
    member_file_meta_dict = {}
    member_file_meta_dict['file_name'] = "client-enrollment.mobileconfig"
    member_file_meta_dict['file_size'] = len(given_mobileconfig_contents)
    member_file_meta_dict['file_object'] = StringIO(given_mobileconfig_contents)
    member_files_array.append(member_file_meta_dict)

    # Identity:
    member_file_meta_dict = {}
    member_file_meta_dict['file_name'] = "client-identity.pem"
    member_file_meta_dict['file_size'] = len(given_pki_contents)
    member_file_meta_dict['file_object'] = StringIO(given_pki_contents)
    member_files_array.append(member_file_meta_dict)

    # Create new archive:
    try:
        tar_file = tarfile.open(tar_file_path,'w')
    except tarfile.TarError:
        common.logging_error("Failed to create archive file at %s." % tar_file_path)
        return None

    # Add files to tar:
    for m in member_files_array:
        try:
            file_info = tarfile.TarInfo(m['file_name'])
            file_info.size = m['file_size']
            if file_info.size == 0:
                common.logging_error("%s appears to be empty." % m['file_name'])
            tar_file.addfile(file_info,m['file_object'])
        except:
            common.logging_error("Failed to add %s to archive." % m['file_name'])

    tar_file.close()

    # Read archive:
    try:
        tar_file = open(tar_file_path,'r')
        attachment_contents = base64.b64encode(tar_file.read())
        tar_file.close()
    except tarfile.TarError:
        common.logging_error("Failed to read newly created archive at %s." % tar_file_path)
        return None

    # Remove archive:
    if os.path.exists(tar_file_path):
        os.remove(tar_file_path)
        common.logging_info("Removed archive: %s." % tar_file_path)

    # Return:
    return attachment_contents

def make_mobileconfig(given_serial,given_ca_cert_p12_data,given_ca_cert_cn):
    '''Generates a configuration profile with a P12 payload containing the given CA P12 data
        and a MCX payload with the ManagedInstalls.plist for the munki_client.
        Returns the XML contents of the config file or None.'''
    common.logging_info("Generating configuration profile for %s." % given_serial)

    # New profile main dict:
    mobileconfig_top_dict = {}
    mobileconfig_top_dict['PayloadVersion'] = int(1)
    mobileconfig_top_dict['PayloadType'] = "Configuration"
    mobileconfig_top_dict['PayloadScope'] = "System"
    mobileconfig_top_dict['PayloadIdentifier'] = "%s.config.profile.munki-enrollment" % config_munki_client.ORGANIZATION_ID_PREFIX
    mobileconfig_top_dict['PayloadUUID'] = str(uuid.uuid4())
    mobileconfig_top_dict['PayloadOrganization'] = config_munki_client.CONFIG_PROFILE_ORG
    mobileconfig_top_dict['PayloadDisplayName'] = config_munki_client.CONFIG_PROFILE_DISPLAY_NAME
    mobileconfig_top_dict['PayloadDescription'] = config_munki_client.CONFIG_PROFILE_DESCRIPTION
    mobileconfig_top_dict['PayloadContent'] = [] # This is an array of other dicts.

    
    # P12 CA Payload:
    payload_p12_dict = {}
    payload_p12_dict['PayloadVersion'] = int(1)
    payload_p12_dict['PayloadType'] = "com.apple.security.pkcs12"
    payload_p12_dict['PayloadUUID'] = str(uuid.uuid4())
    payload_p12_dict['PayloadIdentifier'] = "%s.config.payload.com.apple.security.pkcs12.ca-cert" % config_munki_client.ORGANIZATION_ID_PREFIX
    payload_p12_dict['PayloadDisplayName'] = config_munki_client.P12_CA_DISPLAY_NAME
    payload_p12_dict['PayloadDescription'] = "CA: %s" % given_ca_cert_cn
    payload_p12_dict['PayloadContent'] = plistlib.Data(given_ca_cert_p12_data)
    payload_p12_dict['Password'] = given_serial
    mobileconfig_top_dict['PayloadContent'].append(payload_p12_dict)
    p12_server_ca = None

    # Munki client prefs start with template file read by our configuration:
    mcx_preference_settings = config_munki_client.MUNKI_CLIENT_PREFS_DICT
    # Test for mandatory keys:
    for key in config_munki_client.MUNKI_CLIENT_MANDATORY_KEYS:
        try:
            value = mcx_preference_settings[key]
        except KeyError:
            return None
    # Add key overrides:
    mcx_preference_settings['UseClientCertificate'] = True
    mcx_preference_settings['UseClientCertificateCNAsClientIdentifier'] = False
    mcx_preference_settings['ClientIdentifier'] = 'computers/%s' % given_serial.upper()
    # Random password for the Munki keychain:
    mcx_preference_settings['KeychainPassword'] = str(uuid.uuid4()).replace('-','')
    # Set the keychain name so that it's clear it can be removed as long as the
    # client's identity PEM file is present.
    mcx_preference_settings['KeychainName'] = "munki-temp.keychain"
    
    # Munki config profile payload:
    payload_mcx_munki_client_dict = {}
    payload_mcx_munki_client_dict['PayloadVersion'] = int(1)
    payload_mcx_munki_client_dict['PayloadType'] = "com.apple.ManagedClient.preferences"
    payload_mcx_munki_client_dict['PayloadUUID'] = str(uuid.uuid4())
    payload_mcx_munki_client_dict['PayloadIdentifier'] = "%s.config.payload.com.apple.ManagedClient.preferences.munki" % config_munki_client.ORGANIZATION_ID_PREFIX
    payload_mcx_munki_client_dict['PayloadDisplayName'] = config_munki_client.MUNKI_MCX_PAYLOAD_DISPLAY_NAME
    payload_mcx_munki_client_dict['PayloadDescription'] = "Server: %s" % mcx_preference_settings['SoftwareRepoURL'].replace('https://','').replace('/','')
    payload_mcx_munki_client_dict['PayloadContent'] = {}
    payload_mcx_munki_client_dict['PayloadContent'][config_munki_client.MUNKI_MCX_DEFAULTS_DOMAIN] = {}
    payload_mcx_munki_client_dict['PayloadContent'][config_munki_client.MUNKI_MCX_DEFAULTS_DOMAIN]['Forced'] = [{}]
    payload_mcx_munki_client_dict['PayloadContent'][config_munki_client.MUNKI_MCX_DEFAULTS_DOMAIN]['Forced'][0]['mcx_preference_settings'] = mcx_preference_settings
    mobileconfig_top_dict['PayloadContent'].append(payload_mcx_munki_client_dict)

    # Return XML of the mobileconfig:
    try:
        return plistlib.writePlistToString(mobileconfig_top_dict)
    except xml.parsers.expat.ExpatError, TypeError:
        return None
