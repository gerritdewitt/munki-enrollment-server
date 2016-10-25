#!/usr/bin/env python

# configuration.py
# Munki Enrollment Server
# Configuration used by the Enrollment Server.

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# Project started 2015-06-15.  This file created 2015-07-24.
# 2016-09-19, 2016-10-11, 2016-10-18.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.
# References: See top level Read Me.

import os
import read_configuration as r

class Site(object):
    '''Object containing site specific configuration.'''
    def __init__(self):
        r.read_config_files()
        self.ORGANIZATION_NAME = r.read_config_key('Site','organization_name')
        self.SUB_ORGANIZATION_NAME = r.read_config_key('Site','sub_organization_name')
        self.ORGANIZATION_ID_PREFIX = r.read_config_key('Site','organization_prefix')

class ServerApp(object):
    '''Object containing server app configuration.'''
    def __init__(self):
        r.read_config_files()
        self.PORT = r.read_optional_config_key('ServerApp','port',int(3000))
        # IMPORTANT NOTE REGARDING DEBUG MODE:
        # When true, not only is the top level try-except block
        # skipped, but this web app will bind to any IP address.
        # In production, it should only bind to 127.0.0.1, and client
        # requests should be sent via proxy_pass from the web server
        # where the web server offers HTTPS.  Thus debug mode enables
        # clear text HTTP on any port!
        self.DEBUG_MODE = r.read_optional_config_key('ServerApp','debug_mode',False)
        self.TEMP_DIR = r.read_optional_config_key('ServerApp','temp_dir',"/tmp")
        self.TRANSACTIONS = ['request-enrollment',
                             'transaction-a',
                             'get-group-manifests',
                             'join-manifest',
                             'set-name']
        self.ANON_TRANSACTIONS = ['request-enrollment']

class MunkiManifests(object):
    '''Object containing Munki repository config.'''
    def __init__(self):
        r.read_config_files()
        self.MUNKI_REPO_PATH = r.read_config_key('MunkiManifests','repo_path')
        # Manifests subdir:
        d = r.read_optional_config_key('MunkiManifests','manifests_dirname',"manifests")
        self.MUNKI_MANIFESTS_PATH = os.path.join(self.MUNKI_REPO_PATH,d)
        # Group manifests subdir:
        d = r.read_optional_config_key('MunkiManifests','group_manifests_dirname',"groups")
        self.GROUP_MANIFESTS_PATH = os.path.join(self.MUNKI_MANIFESTS_PATH,d)
        # Computer manifests subdir:
        d = r.read_optional_config_key('MunkiManifests','computer_manifests_dirname',"computers")
        self.COMPUTER_MANIFESTS_PATH = os.path.join(self.MUNKI_MANIFESTS_PATH,d)
        # Misc defaults:
        self.CATALOG_ARRAY = r.read_config_key('MunkiManifests','catalog_array')
        self.DEFAULT_GROUP = r.read_config_key('MunkiManifests','default_group_manifest')
        self.DEFAULT_COMPUTER_NAME_PREFIX = r.read_config_key('MunkiManifests','default_computer_name_prefix')

class CertificateAuthority(object):
    '''Paths and details to access the CA.'''
    def __init__(self):
        r.read_config_files()
        self.CA_PRIVATE_KEY_FILE_PATH = r.read_config_key('CertificateAuthority','private_key_path')
        self.CA_CERT_FILE_PATH = r.read_config_key('CertificateAuthority','cert_path')
        self.CA_PRIVATE_KEY_PASSPHRASE = r.read_config_key('CertificateAuthority','private_key_passphrase')

class ClientCertificate(object):
    '''Object containing details for client certificates.'''
    def __init__(self):
        r.read_config_files()
        self.PRIVATE_KEY_BITS = r.read_config_key('ClientCertificate','private_key_bits')
        self.CSR_SIGNING_HASH_ALGORITHM = r.read_config_key('ClientCertificate','csr_signing_hash_algorithm')
        self.CSR_COUNTRY = r.read_config_key('ClientCertificate','csr_country')
        self.CSR_STATE = r.read_config_key('ClientCertificate','csr_state')
        self.CSR_LOCALE = r.read_config_key('ClientCertificate','csr_locale')
        self.CSR_ORG = r.read_config_key('ClientCertificate','csr_org')
        self.CSR_OU = r.read_config_key('ClientCertificate','csr_ou')
        self.CERT_LIFE_YEARS = r.read_config_key('ClientCertificate','cert_life_years')

class ClientMunkiPrefs(object):
    '''Object containing Munki client prefs.'''
    def __init__(self):
        r.read_config_files()
        self.CONFIG_PROFILE_ORG = r.read_config_key('ClientMunkiPrefs','config_profile_org')
        self.CONFIG_PROFILE_DISPLAY_NAME = r.read_config_key('ClientMunkiPrefs','config_profile_display_name')
        self.CONFIG_PROFILE_DESCRIPTION = r.read_config_key('ClientMunkiPrefs','config_profile_description')
        self.P12_CA_DISPLAY_NAME = r.read_config_key('ClientMunkiPrefs','p12_ca_display_name')
        self.MUNKI_MCX_PAYLOAD_DISPLAY_NAME = r.read_config_key('ClientMunkiPrefs','munki_mcx_payload_display_name')
        self.MUNKI_MCX_DEFAULTS_DOMAIN = r.read_config_key('ClientMunkiPrefs','munki_mcx_defaults_domain')
        self.MUNKI_CLIENT_PREFS_DICT = r.MUNKI_CLIENT_PREFS_DICT
        self.MUNKI_CLIENT_MANDATORY_KEYS = ['ClientCertificatePath',
                                            'ClientKeyPath',
                                            'SoftwareRepoCAPath',
                                            'SoftwareRepoURL']

