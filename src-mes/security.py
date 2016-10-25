#!/usr/bin/env python

# security.py
# Munki Enrollment Server
# Collection of Python methods used by the Enrollment Server.

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# Project started 2015-06-15.  This file created 2015-07-23.
# 2016-09-19, 2016-10-11.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.
# References: See top level Read Me.

import os, base64, sys
from OpenSSL import crypto
# Load our modules:
import common
# Import configuration:
import configuration_classes as config
config_client_pki = config.ClientCertificate()
config_ca = config.CertificateAuthority()

#PRAGMA MARK: GENERAL METHODS

def read_cert_cn(given_cert):
    '''Given any cert object and passphrase, return its subject CN or None.'''
    common.logging_info("Getting CN for given certificate.")
    try:
        return str(given_cert.get_subject().CN)
    except crypto.Error:
        common.logging_error("Could not get the certificate's common name.")
        return None

def read_ca_cert():
    '''Loads CA certificate from the filesystem and returns it as an object.
        Returns None if something went wrong.'''
    common.logging_info("Loading CA certificate.")
    # Check for missing CA certificate:
    if not os.path.exists(config_ca.CA_CERT_FILE_PATH):
        common.logging_error("No CA certificate file found at %s." % config_ca.CA_CERT_FILE_PATH)
        return None
    # Read and load CA certificate:
    try:
        file_object = open(config_ca.CA_CERT_FILE_PATH,'r')
        file_contents = file_object.read()
        file_object.close()
    except IOError:
        return None
    # Return CA cert:
    try:
        return crypto.load_certificate(crypto.FILETYPE_PEM,file_contents)
    except crypto.Error:
        common.logging_error("Could not read CA certificate from %s." % config_ca.CA_CERT_FILE_PATH)
        return None

def generate_private_key():
    '''Generates a private key (RSA).
        Returns the key or None if something went wrong.'''
    common.logging_info("Generating a private key.")
    try:
        key = crypto.PKey()
        return key.generate_key(crypto.TYPE_RSA,config_client_pki.PRIVATE_KEY_BITS)
    except crypto.Error:
        return None

def generate_csr(given_key,given_cn):
    '''Generates a certificate signing request.
        Returns that request or None.'''
    common.logging_info("Generating a certificate signing request for %s." % given_cn)
    # Create X509 object:  Technically this is not a CSR (X509Req) object
    # because we're signing it locally.  Or maybe that's not the reason.
    # Regardless, X509Req objects don't become X509 objects, and only X509
    # objects can added to a PKCS12 container.  We need to do that later.
    # Hence we're using an X509 object.
    try:
        csr = crypto.X509()
        # Set CSR attributes:
        csr.get_subject().C = config_client_pki.CSR_COUNTRY
        csr.get_subject().ST = config_client_pki.CSR_STATE
        csr.get_subject().L = config_client_pki.CSR_LOCALE
        csr.get_subject().O = config_client_pki.CSR_ORG
        csr.get_subject().OU = config_client_pki.CSR_OU
        csr.get_subject().CN = given_cn.upper()
        # Apple Keychain CDSA requires certificate serial attribute:
        # Keychain Access will show an error message, but the profiles
        # tool and Profiles prefs pane will just fail silently.
        csr.set_serial_number(0)
    except crypto.Error:
        return None
    # Set dates:
    try:
        csr.gmtime_adj_notBefore(0)
        csr.gmtime_adj_notAfter(config_client_pki.CERT_LIFE_YEARS*365*24*3600)
    except crypto.Error:
        return None
    # Associate with keypair:
    try:
        csr.set_pubkey(given_key)
    except crypto.Error:
        return None
    # Return:
    return csr

#PRAGMA MARK: CONVERSION METHODS

def pem_to_cert(given_pem):
    '''Given a PEM string, load it and return a certificate object.
        Returns None if something went wrong.'''
    try:
        return crypto.load_certificate(crypto.FILETYPE_PEM,given_pem)
    except crypto.Error:
        logging_error("Could load a certificate from the given PEM string.")
        return None

def make_identity_pem_string(given_key,given_cert,given_ca_cert):
    '''Given objects for client key, client cert, and CA cert,
        extract their contents in PEM format and combine them
        into a single text string.  Return that string or None.'''
    common.logging_info("Generating client identity PEM.")
    try:
        key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM,given_key)
    except crypto.Error:
        common.logging_error("Could not get PEM contents of private key.")
        return None
    try:
        cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM,given_cert)
    except crypto.Error:
        common.logging_error("Could not get PEM contents of client certificate.")
        return None
    try:
        ca_pem = crypto.dump_certificate(crypto.FILETYPE_PEM,given_ca_cert)
    except crypto.Error:
        common.logging_error("Could not get PEM contents of CA certificate.")
        return None
    combined_pem = '%(key_pem)s\n%(cert_pem)s\n%(ca_pem)s' % {'key_pem':key_pem,'cert_pem':cert_pem,'ca_pem':ca_pem}
    return combined_pem

def make_p12_with_ca_cert(given_ca_cert,given_passphrase):
    '''Given CA cert object and passphrase, create a PKCS container
        and return it as data.  Return None if something went wrong.'''
    common.logging_info("Generating PKCS12 store for given CA certificate.")
    p = crypto.PKCS12()
    try:
        p.set_ca_certificates([given_ca_cert])
    except crypto.Error:
        common.logging_error("Could create a p12 object with given CA certificate.")
        return None
    try:
        p12_ca_data = p.export(passphrase=given_passphrase)
    except crypto.Error:
        common.logging_error("Could not export data from p12 object.")
        return None
    return p12_ca_data

#PRAGMA MARK: SIGNING & VERIFICATION METHODS

def sign_with_ca(given_csr,given_ca_cert):
    '''Signs a CSR with the specified CA's private key.
        Returns the signed certificate or None.'''
    common.logging_info("Signing certificate signing request.")
    # Check CSR:
    if not given_csr:
        common.logging_error("Invalid CSR.")
        return None
    # Check CA certificate:
    if not given_ca_cert:
        common.logging_error("Cannot sign CSR - CA certificate error.")
        return None
    # Check for missing CA key file:
    if not os.path.exists(config_ca.CA_PRIVATE_KEY_FILE_PATH):
        common.logging_error("No CA private key file found at %s." % config_ca.CA_PRIVATE_KEY_FILE_PATH)
        return None
    # Read and load CA private key:
    try:
        file_object = open(config_ca.CA_PRIVATE_KEY_FILE_PATH,'r')
        file_contents = file_object.read()
        file_object.close()
    except IOError:
        return None
    try:
        ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM,file_contents,config_ca.CA_PRIVATE_KEY_PASSPHRASE)
    except crypto.Error:
        common.logging_error("Could not read CA private key from %s." % config_ca.CA_PRIVATE_KEY_FILE_PATH)
        return None
    # Set issuer:
    try:
        given_csr.set_issuer(given_ca_cert.get_subject())
    except crypto.Error:
        common.logging_error("Could not set issuer for CSR to CA subject.")
        ca_key = None # safety!
        return None
    # Sign the CSR with the CA's private key:
    try:
        given_csr.sign(ca_key,config_client_pki.CSR_SIGNING_HASH_ALGORITHM)
    except crypto.Error:
        common.logging_error("Could not sign CSR!")
        ca_key = None # safety!
        return None
    # Wipe CA private key and these variables before exiting this method:
    ca_key = None
    file_contents = None
    file_object = None
    # Return signed cert:
    return given_csr

def verify_signed_message(given_message,given_encoded_sig,given_cert):
    '''Given strings for the message, its signature, and a certificate object,
        verify the message.  Returns true or false.'''
    # Decode given signature (expected base64 encoding):
    try:
        decoded_sig = base64.b64decode(given_encoded_sig)
    except:
        common.logging_error("Could not interpret encoded signature.")
        return False
    # Verify the signature:
    try:
        # OpenSSL is funny.  A successful crypto.verify() returns a None object!
        crypto.verify(given_cert,decoded_sig,given_message,config_client_pki.CSR_SIGNING_HASH_ALGORITHM)
        return True
    except crypto.Error:
        common.logging_error("Message fails verification.")
        return False

