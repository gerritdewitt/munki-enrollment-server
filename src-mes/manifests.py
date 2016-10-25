#!/usr/bin/env python

# manifests.py
# Munki Enrollment Server
# Collection of Python methods used by the Enrollment Server.

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# Project started 2015-06-15.  This file created 2015-07-24.
# 2016-09-19, 2016-10-11.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.
# References: See top level Read Me.

import os, plistlib, xml, glob
# Load our modules:
import common
# Import configuration:
import configuration_classes as config
munki_repo = config.MunkiManifests()

def get_computer_manifest_details(given_computer_manifest_name):
    '''Checks for the presence and validity of an existing manifest for this client in the repository.
        Reads name from the metadata and group from the included_manifest key.'''
    # Defaults:
    computer_manifest_details_dict = {}
    computer_manifest_details_dict['exists'] = False
    computer_manifest_details_dict['name'] = ''
    included_manifests = []
    computer_manifest_details_dict['group'] = ''
    associated_group_valid = False
    # Check for this computer's manifest:
    computer_manifest_path = os.path.join(munki_repo.COMPUTER_MANIFESTS_PATH,given_computer_manifest_name)
    if os.path.exists(computer_manifest_path):
    # Read the manifest:
        try:
            computer_manifest_dict = plistlib.readPlist(computer_manifest_path)
            computer_manifest_details_dict['exists'] = True
        except xml.parsers.expat.ExpatError:
            pass
    # Read name and included_manifests key:
    if computer_manifest_details_dict['exists']:
        try:
            computer_manifest_details_dict['name'] = computer_manifest_dict['_metadata']['computer_name']
        except KeyError:
            pass
        try:
            included_manifests = computer_manifest_dict['included_manifests']
        except KeyError:
            pass
    # Parse included manifests to determine the associated group:
    for included_manifest_name in included_manifests:
        if included_manifest_name.find('groups/') != -1:
            try:
                computer_manifest_details_dict['group'] = included_manifest_name.split('/')[1]
                break
            except IndexError:
                pass
    # Validate associated group:
    if computer_manifest_details_dict['group']:
        group_manifest_path = os.path.join(munki_repo.GROUP_MANIFESTS_PATH, computer_manifest_details_dict['group'])
        if os.path.exists(group_manifest_path):
            try:
                group_manifest_dict = plistlib.readPlist(group_manifest_path)
                if group_manifest_dict:
                    associated_group_valid = True
            except xml.parsers.expat.ExpatError:
                pass
    if not associated_group_valid:
        computer_manifest_details_dict['group'] = ''
    # Return:
    return computer_manifest_details_dict

def make_computer_manifest(given_serial):
    '''Checks for the presence and validity of an existing manifest for this client in the repository.
        Creates a new manifest if an existing one is not found or is invalid.'''
    # Filesystem path for this computer's manifest:
    computer_manifest_name = given_serial.upper() # if not already
    computer_manifest_path = os.path.join(munki_repo.COMPUTER_MANIFESTS_PATH,computer_manifest_name)
    # Control variable: should a new manifest be created?
    # Assume yes, unless an existing manifest is found and is valid.
    should_create_new_client_manifest = True

    # Catch missing computer manifests directory:
    if not os.path.exists(munki_repo.COMPUTER_MANIFESTS_PATH):
        common.logging_error("Computers manifests directory not found at %s." % munki_repo.COMPUTER_MANIFESTS_PATH)
        raise
    
    # Check existing manifest for this client:
    if os.path.exists(computer_manifest_path):
        common.logging_info("Manifest for %s already in repository. Checking it." % computer_manifest_name)
        try:
            computer_manifest_dict = plistlib.readPlist(computer_manifest_path)
            # Manifest already exists; do not overwrite if it's a valid dict!
            if computer_manifest_dict:
                should_create_new_client_manifest = False
                common.logging_info("Manifest for %s should be left alone." % computer_manifest_name)
        except xml.parsers.expat.ExpatError:
            common.logging_error("Manifest for %s is invalid. Will recreate." % computer_manifest_name)

    # Build a new client manifest if required:
    if should_create_new_client_manifest:
        common.logging_info("Creating new manifest for %s." % computer_manifest_name)
        computer_manifest_dict = {}
        computer_manifest_dict['managed_installs'] = []
        computer_manifest_dict['managed_uninstalls'] = []
        computer_manifest_dict['catalogs'] = munki_repo.CATALOG_ARRAY
        computer_manifest_dict['included_manifests'] = ['groups/%s' % munki_repo.DEFAULT_GROUP]
        try:
            plistlib.writePlist(computer_manifest_dict,computer_manifest_path)
        except TypeError:
            common.logging_error("Failed to write manifest for %s." % computer_manifest_name)

def list_group_manifests():
    '''Scans the munki repository for manifests that we designate as computer groups.
        Returns an array of dictionaries, each dict representing a group.'''
    # Catch missing manifests path:
    if not os.path.exists(munki_repo.GROUP_MANIFESTS_PATH):
        common.logging_error("Missing group manifests directory.")
        return False, [] # empty list
    path_glob = '%s/*' % str(munki_repo.GROUP_MANIFESTS_PATH)
    common.logging_info("Listing group manifests: %s" % path_glob)
    try:
        search_results_path_array = glob.glob(path_glob)
    except:
        common.logging_error("Glob error while listing group manifests directory.")
        return False, [] # empty list
    # Go through the returned group manifests, validating them and reading metadata:
    groups_array = []
    for manifest_path in search_results_path_array:
        try:
            manifest_dict = plistlib.readPlist(manifest_path)
            have_valid_manifest = True
        except xml.parsers.expat.ExpatError:
            # Skip manifests that cannot be parsed as plists:
            common.logging_error("Skipping invalid group manifest: %s" % manifest_path)
            have_valid_manifest = False
            pass
        if have_valid_manifest:
            # Build dictionary representing this group:
            group_details_dict = {}
            # At least the name is present:
            group_details_dict['name'] = os.path.basename(manifest_path)
            # Assign defaults unless we can override them with metadata:
            group_details_dict['display_name'] = group_details_dict['name']
            group_details_dict['description'] = group_details_dict['name']
            group_details_dict['computer_name_prefix'] = munki_repo.DEFAULT_COMPUTER_NAME_PREFIX
            # Check for metadata in the manifest:
            try:
                manifest_metadata_dict = manifest_dict['_metadata']
                have_manifest_metadata = True
            except KeyError:
                have_manifest_metadata = False
                pass
            # Attempt to read various metadata keys:
            if have_manifest_metadata:
                try:
                    group_details_dict['display_name'] = manifest_metadata_dict['display_name']
                except KeyError:
                    pass
                try:
                    group_details_dict['description'] = manifest_metadata_dict['description']
                except KeyError:
                    pass
                try:
                    group_details_dict['computer_name_prefix'] = manifest_metadata_dict['computer_name_prefix']
                except KeyError:
                    pass
            # Append group details dict to ths groups array:
            groups_array.append(group_details_dict)
    # Catch empty groups_array:
    if len(groups_array) == 0:
        return False, [] # empty list
    # Return group list:
    return True, groups_array

def join_group_manifest(given_computer_manifest_name,given_group_manifest_name):
    '''Modifes a computer manifest's included_manifests key to include the name of a group manifest,
        effectively making the computer a member of the group and its parent groups.
        Both manifests must be present and valid plists.  Returns true if successful, false otherwise.'''
    # Filesystem paths for manifests:
    given_computer_manifest_name = given_computer_manifest_name.upper() # if not already
    computer_manifest_path = os.path.join(munki_repo.COMPUTER_MANIFESTS_PATH,given_computer_manifest_name)
    group_manifest_path = os.path.join(munki_repo.GROUP_MANIFESTS_PATH,given_group_manifest_name)
    
    # Catch missing manifests:
    if not os.path.exists(computer_manifest_path):
        common.logging_error("Computer manifest not found at %s." % computer_manifest_path)
        return False
    if not os.path.exists(group_manifest_path):
        common.logging_error("Group manifest not found at %s." % group_manifest_path)
        return False

    # Load manifests:
    try:
        computer_manifest_dict = plistlib.readPlist(computer_manifest_path)
    except xml.parsers.expat.ExpatError:
        common.logging_error("Computer manifest %s is invalid." % given_computer_manifest_name)
        return False
    try:
        group_manifest_dict = plistlib.readPlist(group_manifest_path)
    except xml.parsers.expat.ExpatError:
        common.logging_error("Group manifest %s is invalid." % given_group_manifest_name)
        return False

    # Modify computer manifest and save it:
    common.logging_info("Adding %(computer)s to %(group)s." % {'computer':given_computer_manifest_name,'group':given_group_manifest_name})
    # Make sure these stay empty; data should come from included (group) manifest only:
    computer_manifest_dict['managed_installs'] = []
    computer_manifest_dict['managed_uninstalls'] = []
    computer_manifest_dict['catalogs'] = munki_repo.CATALOG_ARRAY
    # Add to group:
    computer_manifest_dict['included_manifests'] = []
    computer_manifest_dict['included_manifests'].append('groups/%s' % given_group_manifest_name)
    try:
        plistlib.writePlist(computer_manifest_dict,computer_manifest_path)
        return True
    except TypeError:
        common.logging_error("Failed to write manifest for %s." % given_computer_manifest_name)
        return False

def write_metadata_to_manifest(given_computer_manifest_name,given_metadata_key,given_metadata_value):
    '''Modifes the given computer manifest's _metadata dict, adding (overwriting) the given key and value.
        Given manifest must be present and a valid plist.  Returns true if successful, false otherwise.'''
    # Filesystem paths for the manifest:
    given_computer_manifest_name = given_computer_manifest_name.upper() # if not already
    computer_manifest_path = os.path.join(munki_repo.COMPUTER_MANIFESTS_PATH,given_computer_manifest_name)
    
    # Catch missing manifest:
    if not os.path.exists(computer_manifest_path):
        common.logging_error("Computer manifest not found at %s." % computer_manifest_path)
        return False
    
    # Load manifest:
    try:
        computer_manifest_dict = plistlib.readPlist(computer_manifest_path)
    except xml.parsers.expat.ExpatError:
        common.logging_error("Computer manifest %s is invalid." % given_computer_manifest_name)
        return False

    # Load manifest metadata or start with blank:
    try:
        manifest_metadata_dict = computer_manifest_dict['_metadata']
    except KeyError:
        manifest_metadata_dict = {}

    # Modify metadata dict:
    common.logging_info("Adding %(key)s to %(manifest)s." % {'key':given_metadata_key,'manifest':given_computer_manifest_name})
    manifest_metadata_dict[given_metadata_key] = given_metadata_value
    computer_manifest_dict['_metadata'] = manifest_metadata_dict

    # Save manifest:
    try:
        plistlib.writePlist(computer_manifest_dict,computer_manifest_path)
        return True
    except TypeError:
        common.logging_error("Failed to write manifest for %s." % given_computer_manifest_name)
        return False
