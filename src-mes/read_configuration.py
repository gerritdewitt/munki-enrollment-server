#!/usr/bin/env python

# read_configuration.py
# Munki Enrollment Server
# Configuration used by the Enrollment Server.

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# Project started 2015-06-15.
# 2016-10-11, 2016-10-18.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.
# References: See top level Read Me.

import os, plistlib, xml, sys, logging

def read_config_key(given_parent_key,given_child_key):
    '''Returns value for key in CONFIG_FILE_ROOT_DICT or exits 1 on failure.'''
    try:
        return CONFIG_FILE_ROOT_DICT[given_parent_key][given_child_key]
    except KeyError:
        logging.error("Missing key %(child_key)s in %(parent_key)s" % {"child_key":given_child_key,"parent_key":given_parent_key})
        sys.exit(1)

def read_optional_config_key(given_parent_key,given_child_key,given_default_value):
    '''Returns value for key in CONFIG_FILE_ROOT_DICT or returns the given default value on failure.'''
    try:
        return CONFIG_FILE_ROOT_DICT[given_parent_key][given_child_key]
    except KeyError:
        logging.error("Missing key %(child_key)s in %(parent_key)s; defaulting to \"%(default_value)s\"." % {"child_key":given_child_key,"parent_key":given_parent_key,"default_value":given_default_value})
        return given_default_value

def read_config_files():
    '''Loads config files.'''
    global CONFIG_FILE_ROOT_DICT
    global MUNKI_CLIENT_PREFS_DICT
    parent_dir = os.path.dirname(os.path.realpath(__file__))
    config_file_path = os.path.join(parent_dir,'configuration.plist')
    munki_client_prefs_path = os.path.join(parent_dir,'munki_client_prefs.plist')
    if not os.path.exists(config_file_path):
        logging.error("Missing config file: %s" % config_file_path)
        sys.exit(1)
    if not os.path.exists(munki_client_prefs_path):
        logging.error("Missing config file: %s" % munki_client_prefs_path)
        sys.exit(1)
    try:
        CONFIG_FILE_ROOT_DICT = plistlib.readPlist(config_file_path)
    except xml.parsers.expat.ExpatError:
        logging.error("Could not parse file: %s" % config_file_path)
        sys.exit(1)
    try:
        MUNKI_CLIENT_PREFS_DICT = plistlib.readPlist(munki_client_prefs_path)
    except xml.parsers.expat.ExpatError:
        logging.error("Could not parse file: %s" % munki_client_prefs_path)
        sys.exit(1)