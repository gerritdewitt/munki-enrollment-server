#!/usr/bin/env python

# devices.py
# Munki Enrollment Server
# Collection of Python methods used by the Enrollment Server.

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# Project started 2015-06-15.  This file created 2016-09-19.
# 2016-09-19.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.
# References: See top level Read Me.

import logging
# Import configuration:
import configuration_classes as config
config_app = config.ServerApp()

def validate_serial_number(given_serial):
    '''Performs a sanity check on the serial.  Placeholder for now.'''
    # Convert to uppercase, strip spaces and new lines, and validate:
    given_serial = given_serial.replace(' ','').replace('\n','').upper()

    return given_serial