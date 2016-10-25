#!/usr/bin/env python

# common.py
# Munki Enrollment Server
# Collection of Python methods used by the Enrollment Server.

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# Project started 2015-06-15.  This file created 2015-07-23.
# 2016-09-19.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.
# References: See top level Read Me.

import logging
# Import configuration:
import configuration_classes as config
config_app = config.ServerApp()

def logging_info(given_message):
    logging.info(given_message)
    if config_app.DEBUG_MODE:
        print '  %s' % given_message

def logging_error(given_message):
    logging.error(given_message)
    if config_app.DEBUG_MODE:
        print '  %s' % given_message