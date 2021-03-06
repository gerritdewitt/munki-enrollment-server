About
----------
The Munki Enrollment Server (MES) is a web application written in Python.  It is the server compliment to the Munki Enrollment Client (MEC), providing a method of enrolling Mac systems with Munki for certificate-based communication thereafter.

Communication between the MEC and the MES is encrypted in transit with HTTPS.  Based on input from the Munki Enrollment Client (MEC), it handles:
   - creating a computer manifest for an enrolling computer if necessary,
   - generating client PKI materials (private keys, certificates) from its local CA and returning them to the client,
   - associating computer manifests with group manifests by modifying their _included_manifests_ keys,
   - providing clients with their manifest data and a list of available group manifests.

A concept of a server like this appears to have originated around 2012 with Cody Eding's munki-enroll web app.

The MES is written in Python and distributed with its own virtual environments.  The MES is designed to be hosted on **Linux**, with all of its dependencies in a single container.  It could be ported to run in other environments; for example, in a Docker environment on another platform.

Certificate Authority Requirement
----------
The MES requires access to a local CA (its private key and certificate).  Refer to the _Munki_CA_ReadMe.md_ file in the _Documentation_ folder for more details.

Building
----------
### Steps ###
Run the _build-script.sh_ on a **Linux** system.  For example, we build on RHEL.  The _build-script.sh_ needs Internet access.  It grabs current versions of the open source items it needs from the Internet.

This script is interactive.  When building, the script requests the following parameters:
   - A version number.  This is an arbitrary string for your own internal versioning purposes.
   - Details for the system account under which the MES will run.  It is possible to run the MES as root, but that's not the best idea.  We run the MES with the privileges of another account whose details you specify at build time:
      - An *account name* for the system user; we recommend *munki-enrollment-server*.
      - The UNIX UID number for this system account.  For example, 502.  Pick a UID for a user not already used by the system.

The build script produces a “package root” tarball for installation.  Refer to the Installing section for how-to.

### Special Build Considerations ###
   - If hosting the Munki repository on a mounted NFS volume from another server, take special care to make sure that a user with the same UID is present on that server with appropriate access:
      - Example: *munki-enrollment-server* with UID 502 is configured on the MES server.  The repository server needs a user with UID 502 having access to the Munki repository:
         - read-only access to the entire Munki repository
         - read and write access to the _computers_ subdirectory of the manifests folder in the Munki repository
   - The system user name and UID are embedded in the installable “package root” tarball.  If those need to be changed, the easiest thing to do is rebuild the MES.
   - For the sake of clarity, the build script does *not* create the system user account on the box where you build.  It simply updates the _init-script-template.sh_ so that the _init-script.sh_ creates that account on the server on which you install the MES.

Installing
----------
1. Copy the package root tarball to the target server and expand it in a directory of your choosing.
2. Edit or restore these configuration files for the MES.  Notes for each config file are in XML comments in each file.
   - *&lt;container&gt;/mes_virtualenv/mes/configuration.plist*: Overall server config
   - *&lt;container&gt;/mes_virtualenv/mes/munki_client_prefs.plist*: ManagedInstalls.plist for clients
3. Run the _init-script.sh_ with the _install_ argument as root; for example:
<pre>
tar -xvf munki-enrollment-server-2016.09.tgz
sudo ./munki-enrollment-server/init-script.sh install
</pre>
4. When installing, the script will pause and give you an opportunity to edit or restore the configuration files described in step 2 if you haven't done so already.

To upgrade or install a new version of the package, simpy repeat the installation steps.

### Security Notes ###
The Munki Enrollment Server _could_ run as root, but we run it with a designed user account called _munki-enrollment-server_ for added security.

The _munki-enrollment-server_ user account needs to have access to the Munki repository as specified here.  Note access can be granted by virtue of it being a member of a group, and regular POSIX permissions or POSIX ACLs may be set on the Munki repository:
   - *Munki Repository*:  The MES should have read and execute permissions to the top-level of the munki repository.
      - *Manifests Directory*:  The MES should have read, write, and execute permissions to the _manifests_ repository therein.
   - *Private key for the CA*:  The MES needs to have read permission to the CA's private key.  This key is used to sign the certificates that it dispenses to clients.

Unless running in DEBUG mode, the MES only binds to 127.0.0.1:3000.  Thus, requests from clients must go through a “front end” reverse proxy web server, where you can perform authentication if desired.

Authors & Sources
----------
### By GSU ###
- The following items were created by Gerrit DeWitt (gdewitt@gsu.edu).
   - This file, _ReadMe.md_
   - Other notes in the _Documentation_ directory
   - The _build-script.sh_
   - The _init-script-template.sh_ (and, consequently, the _init-script.sh_ as generated by the _build-script.sh_)
   - The various Python scripts that compose the MES (in _src-mes_).
      - The MEC and MES were created by Gerrit DeWitt (gdewitt@gsu.edu), but the overall idea for the project is not novel.  For example, a project called “Munki Manifest Selector” (noted in Sources) captures the overall design goal.
   - The various property list examples included with the MES (in _src-mes_).
- This container was compiled by Gerrit DeWitt (gdewitt@gsu.edu) using other open source items.  For license terms, authors, and references, refer to the Sources section.
- Special thanks to Jane Eason (jeason@gsu.edu) for pointers and assistance with managing process PIDs on Linux.

### General Reference Notes and Public How-To ###
Omitting items that are obviously in the public domain or for which more than a few references can be found, the following publicly documented methods and how-to were consulted during the creation of the Munki Enrollment Server.

1. Conceptual Inspiration:
   - Munki Manifest Selector: https://denisonmac.wordpress.com/2013/02/09/munki-manifest-selector
   - Munki Manifest Selector: https://github.com/buffalo/Munki-Manifest-Selector
   - Discussion About Manifest Selector: https://groups.google.com/forum/#!topic/munki-dev/kd0xL-TtiGA
   - Munki Enroll: https://github.com/grahampugh/munki-enroll
   - Munki Enroll: https://github.com/edingc/munki-enroll/blob/master/munki-enroll/enroll.php

2. Munki:
   - https://github.com/munki/munki/wiki/Manifests
   - https://code.google.com/p/munki/wiki/configuration
   - https://github.com/munki/munki/wiki/Preferences

3. Creating _init_ Scripts
   - http://www.tldp.org/HOWTO/HighQuality-Apps-HOWTO/boot.html
   - https://blog.hazrulnizam.com/create-init-script-centos-6/
   - https://gist.github.com/TheMengzor/968e5ea87e99d9c41782
   - https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/s2-services-chkconfig.html

4. Configuration Profile Reference
   - Apple Specification: https://developer.apple.com/library/content/featuredarticles/iPhoneConfigurationProfileRef/Introduction/Introduction.html
   - Munki Config Profile Example: https://groups.google.com/forum/#!topic/munki-dev/WkePlyLpVrE

5. Python:
   - https://docs.python.org/2/library/base64.html
   - https://docs.python.org/2/library/plistlib.html
   - https://docs.python.org/2/library/glob.html
   - https://docs.python.org/2/library/uuid.html
   - tarfile: https://docs.python.org/2/library/tarfile.html
      - examples: https://pymotw.com/2/tarfile/
   - Flask
      - Quickstart Guide: http://flask.pocoo.org/docs/0.10/quickstart/
      - Accessing POST Data Example: http://code.runnable.com/UhLMQLffO1YSAADK/handle-a-post-request-in-flask-for-python
      - Accessing POST Data Example: http://stackoverflow.com/questions/12551526/retrieving-specific-post-data-in-flask
      - How to Set Content-Type of Response: http://stackoverflow.com/questions/11773348/python-flask-how-to-set-content-type
      - Downloading a Generated File: http://code.runnable.com/UiIdhKohv5JQAAB6/how-to-download-a-file-generated-on-the-fly-in-flask-for-python
      - Function Did Not Return Response Error: http://stackoverflow.com/questions/18211942/flask-view-return-error-view-function-did-not-return-a-response
      - StringIO: http://stackoverflow.com/questions/141449/how-do-i-wrap-a-string-in-a-file-in-python
      - Syntax for Multiple Substitutions in a String: http://stackoverflow.com/questions/4435152/python-about-multiple-s-in-a-string
   - pyOpenSSL
      - Reference: https://pyopenssl.readthedocs.io/en/latest/api/crypto.html
      - Generating a Private Key and CSR Example: http://stackoverflow.com/questions/26290295/creating-a-csr-request-with-a-challengepassword-in-pyopenssl
      - Generating a Private Key and CSR Example: https://skippylovesmalorie.wordpress.com/2010/02/12/how-to-generate-a-self-signed-certificate-using-pyopenssl/
      - Generating a Private Key and CSR Example: http://nullege.com/codes/show/src%40s%40a%40salt-HEAD%40salt%40modules%40tls.py/217/OpenSSL.crypto.X509.set_pubkey/python
      - Reading from PEM Example: http://stackoverflow.com/questions/14565597/pyopenssl-reading-certificate-pkey-file
      - Signing CSR Example: http://blog.tunnelshade.in/2013/06/sign-using-pyopenssl.html
      - Dumping PEM Examples: http://nullege.com/codes/search/OpenSSL.crypto.dump_certificate
      - Verifying Signed Data Example: http://stackoverflow.com/questions/12146985/verify-signature-with-pyopenssl

6. Misc
   - http://stackoverflow.com/questions/584894/sed-scripting-environment-variable-substitution
   - http://docs.python-guide.org/en/latest/dev/virtualenvs/
   - http://stackoverflow.com/questions/1063347/passing-arrays-as-parameters-in-bash
   - https://github.com/pypa/virtualenv/issues/92
   - http://serverfault.com/questions/529287/rsync-creates-a-directory-with-the-same-name-inside-of-destination-directory
   - https://virtualenv.pypa.io/en/stable/reference/
   - http://wiki.bash-hackers.org/howto/conffile
   - http://unix.stackexchange.com/questions/74185/how-can-i-prevent-grep-from-showing-up-in-ps-results
   - http://man7.org/linux/man-pages/man1/getent.1.html
   - http://www.tecmint.com/add-users-in-linux/
   - http://www.computerhope.com/unix/userdel.htm
   - http://unix.stackexchange.com/questions/196907/proxy-nginx-shows-a-bad-gateway-error
   
### Software ###
1. PyPy Runtime: Created by various authors
   - https://github.com/squeaky-pl/portable-pypy#portable-pypy-distribution-for-linux and http://doc.pypy.org/en/latest/
   - Serves as a standalone, pre-compiled Python 2.7 runtime so we do not have to depend on the version of Python included with the base OS.
   - License for _pypy_: MIT, https://bitbucket.org/pypy/pypy/src/default/LICENSE
   - License for Python 2.7: Python License, https://www.python.org/download/releases/2.7/license/
   - This pypy runtime includes several standard Python modules (the standard Python library).
      - Modules are stored in the _site-packages_ directory in each Python virtual environment.
      - Many standard modules use the Python License.
      - For terms specific to certain modules, or for author information, search for the module by name at _docs.python.org_ or at the Python Package Index site (_pypi.python.org_).
2. Flask: Written and maintained by Armin Ronacher and various contributors.
   - http://flask.pocoo.org
   - License: BSD, http://flask.pocoo.org/docs/0.11/license/
3. Werkzeug: Written and maintained by Armin Ronacher et. al.
   - http://werkzeug.pocoo.org, https://pypi.python.org/pypi/Werkzeug
   - License: BSD, http://werkzeug.pocoo.org
4. Jinja2: Written and maintained by Armin Ronacher et. al.
   - http://jinja.pocoo.org, https://pypi.python.org/pypi/Jinja2
   - License: BSD, http://jinja.pocoo.org
5. MarkupSafe: Written and maintained by Armin Ronacher and contributors.
   - https://pypi.python.org/pypi/MarkupSafe, https://github.com/pallets/markupsafe
   - License: BSD, https://github.com/pallets/markupsafe/blob/master/LICENSE  
6. itsdangerous: Written and maintained by Armin Ronacher and the Django Software Foundation
   - https://pypi.python.org/pypi/itsdangerous, http://pythonhosted.org/itsdangerous/, https://github.com/pallets/itsdangerous
   - License: BSD, https://github.com/pallets/itsdangerous/blob/master/LICENSE
7. pyOpenSSL: Created by Martin Sjögren, Jean-Paul Calderone, et. al; maintained by Hynek Schlawack
   - https://pypi.python.org/pypi/pyOpenSSL, https://pyopenssl.readthedocs.io/en/latest/, https://github.com/pyca/pyopenssl
   - License: Apache License, Version 2.0, https://github.com/pyca/pyopenssl/blob/master/LICENSE
8. cryptography: Created by many individual contributors
   - https://pypi.python.org/pypi/cryptography, https://cryptography.io/en/latest/, https://github.com/pyca/cryptography
   - License: Apache License, Version 2.0 or BSD, https://github.com/pyca/cryptography/blob/master/LICENSE
9. six: Created by Benjamin Peterson
   - https://pypi.python.org/pypi/six, https://pythonhosted.org/six/, https://bitbucket.org/gutworth/six
   - License: MIT
10. ipaddress: Created by Philipp Hagemeister
   - https://pypi.python.org/pypi/ipaddress, https://github.com/phihag/ipaddress
   - License: Python Software Foundation License, https://github.com/phihag/ipaddress/blob/master/LICENSE
11. enum34: Created by Ethan Furman
   - https://pypi.python.org/pypi/enum34, https://bitbucket.org/stoneleaf/enum34
   - License: BSD, https://bitbucket.org/stoneleaf/enum34/src/f24487b45cd041fc9406d67441d2186ac70772b7/enum/LICENSE?at=default&fileviewer=file-view-default
12. idna: Created by Kim Davies
   - https://pypi.python.org/pypi/idna, https://github.com/kjd/idna
   - License: BSD-like, https://github.com/kjd/idna/blob/master/LICENSE.rst
13. pyasn1: Created by Ilya Etingof. Copyright holder Schneider Electric Buildings AB.  Maintained by SNMP Laboratories.
   - https://pypi.python.org/pypi/pyasn1, https://github.com/kimgr/asn1ate, https://sourceforge.net/projects/pyasn1/, http://pyasn1.sourceforge.net
   - License: BSD, https://github.com/kimgr/asn1ate/blob/master/LICENSE.txt
14. nginx: Written and maintained by Igor Sysoev and Nginx, Inc.
   - http://nginx.org/en/, http://nginx.org/packages/rhel/6/x86_64/RPMS/
   - License: BSD, http://nginx.org/LICENSE


Organization
----------
Top level items in this repository are:
   - _build-script.sh_: A shell script that builds a “container” for deployment to a server.  It needs Internet access to download the various components.
   - _init-script-template.sh_: A shell script that serves as a template for the _init-script.sh_ included in the container that's produced.
   - _ReadMe.md_ and _Documentation_: This file and other documentation.
   - _src-mes_: A directory containing Python scripts and configuration files that compose the MES.  These are moved into a Python virtual environment by the _build-script.sh_.

When built, the NetBoot server container has the following layout:
   - _build.log_: The build log created by the _build-script.sh_.
   - _init-script.sh_: The shell script responsible for loading and installing the software.  Created by the _build-script.sh_ from _init-script-template.sh_.
   - _mes_virtualenv_: Portable pypy virtual environment for BSDPy and its dependencies.
      - _mes_: Code and configuration files for the MES.  Some configuration plist files are stored here, too:
         - *configuration.plist*
         - *munki_client_prefs.plist*

Methods
----------
### Python Dependencies ###
Python dependencies are those modules not included with the pypy runtime by default are sourced and added when the _build-script.sh_ runs.  It downloads and installs the necessary dependencies in the virtual environment it creates.  This virtual environment is created using tools included with _pypy_; _pip_ is the method for obtaining the dependencies.
