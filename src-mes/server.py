#!/usr/bin/env python

# server.py
# Munki Enrollment Server
# A Flask webapp for enrolling Mac systems for management via Munki.
# Performs various actions in response to HTTP POSTs initiated from client side scripts.

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# Project started 2015-06-15.
# 2016-09-19.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.
# References: See top level Read Me.

import os, plistlib, xml
from flask import Flask, request, make_response
app = Flask(__name__)
# Load our modules:
import common
import security
import enrollment
import manifests
# Import configuration:
import configuration_classes as config
config_site = config.Site()
config_server_app = config.ServerApp()

# Simple app to handle post data:
@app.route("/enroll",methods=['POST'])
def process_request():
    '''Method called when a request is sent to this web app.'''
    # Defaults:
    # Default response type is plist unless set otherwise:
    response_is_tar_file = False
    response_attachment = None
    response_dict = {}
    response = None
    # Get HTTP POST variables:
    # All interactions must have a command POST variables.
    try:
        command = request.form['command']
    except NameError, KeyError:
        common.logging_error("No command sent in POST.")
        return None
    # Toss unrecognized commands:
    if command not in config_server_app.TRANSACTIONS:
        return None

    # Handle authentication if required:
    if command not in config_server_app.ANON_TRANSACTIONS:
        # Grab additional POST variables:
        try:
            message = request.form['message']
        except KeyError:
            common.logging_error("Message not sent in POST.")
            return None
        try:
            signature = request.form['signature']
        except KeyError:
            common.logging_error("Signature not sent in POST.")
            return None
        try:
            cert_pem_str = request.form['certificate']
        except KeyError:
            common.logging_error("Certificate not sent in POST.")
            return None
        # Load certificate:
        client_cert = security.pem_to_cert(cert_pem_str)
        if not client_cert:
            common.logging_error("Certificate data is invalid!")
        # Determine computer's manifest name by reading the CN of its certificate.
        computer_manifest_name = security.read_cert_cn(client_cert).upper()
        if not computer_manifest_name:
            return None
        # Authentication: Verify signed message using certificate's public key.
        if not security.verify_signed_message(message,signature,client_cert):
            common.logging_error("Authentication error: failed to verify the signed message.")
            return None

    # Handle command:
    if command == 'request-enrollment':
        client_serial = request.form['message']
        common.logging_info("Processing enrollment request for %s..." % client_serial)
        response_attachment = enrollment.do_enrollment(client_serial)
        if not response_attachment:
            common.logging_error("Invalid tar file returned by do_enrollment!")
            return None
        response_is_tar_file = True
    elif command == 'transaction-a':
        common.logging_info("Processing transaction A...")
        response_dict['computer_manifest'] = manifests.get_computer_manifest_details(computer_manifest_name)
        ignored,response_dict['group_manifests_array'] = manifests.list_group_manifests()
    elif command == 'transaction-b':
        common.logging_info("Processing transaction B...")
        response_dict['joined_group'] = False
        response_dict['recorded_name'] = False
        try:
            message_dict = plistlib.readPlistFromString(message)
        except xml.parsers.expat.ExpatError:
            message_dict = {}
        try:
            group_manifest_name = message_dict['group_manifest_name']
            response_dict['joined_group'] = manifests.join_group_manifest(computer_manifest_name,group_manifest_name)
        except KeyError:
            pass
        try:
            desired_computer_name = message_dict['desired_computer_name']
            response_dict['recorded_name'] = manifests.write_metadata_to_manifest(computer_manifest_name,'computer_name',desired_computer_name)
        except KeyError:
            pass
        common.logging_info("Completed transaction B.")
    elif command == 'join-manifest': # DEPRECATED!
        common.logging_info("Processing request to join a group manifest...")
        group_manifest_name = message
        response_dict['result'] = manifests.join_group_manifest(computer_manifest_name,group_manifest_name)
        common.logging_info("Completed request to join a group manifest.")
    elif command == 'set-name': # DEPRECATED!
        common.logging_info("Processing request to store computer name...")
        desired_computer_name = message
        response_dict['result'] = manifests.write_metadata_to_manifest(computer_manifest_name,'computer_name',desired_computer_name)
        common.logging_info("Completed request to store computer name.")

    # Process responses:
    if response_is_tar_file and response_attachment:
        common.logging_info("Processing response: tar file.")
        response = make_response(response_attachment)
        response.headers['Content-Disposition'] = "attachment"
    elif response_dict:
        common.logging_info("Processing response: plist.")
        try:
            response_plist_str = plistlib.writePlistToString(response_dict)
        except xml.parsers.expat.ExpatError, TypeError:
            response_plist_str = ''
        if response_plist_str:
            response = make_response(response_plist_str)
    # Return response:
    if not response:
        return None
    return response

# Launch:
if __name__ == "__main__":
    if config_server_app.DEBUG_MODE:
        print "WARNING: Web app is running in debug mode!"
        app.run(host="0.0.0.0",port=config_server_app.PORT,debug=True)
    else:
        try:
            app.run(host="127.0.0.1",port=config_server_app.PORT,debug=False)
        except:
            common.logging_error("Generic error.  The enrollment server could not complete the request.")
