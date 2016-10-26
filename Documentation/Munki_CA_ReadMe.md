Certificate Authority Requirement
----------
The MES requires access to a local CA infrastructure, namely a certificate and private key for the enrollment CA, to be installed on the same server as the MES.

This document describes a simple method to create a local CA on RHEL Linux which you can deploy to the MES server(s).  Alternatively, you can create CA materials yourself and move them to the MES server.

For simplicity, this document describes using one Munki CA to:
   - Vend client certificates and keys, and
   - Configure HTTPS for the Munki repo with a server certifcate

Setup Example
----------
### First Steps ###
1.  For this example, we'll use _/opt/munki-ca_ as the path for the Munki CA.  Create these directories and paths.  Note that the newcerts dir has to exist or openssl will complain.
<pre>
sudo -s
mkdir /opt/munki-ca/{certs,crl,private,newcerts}
touch /opt/munki-ca/index.txt
echo 1000 > /opt/munki-ca/serial
exit
</pre>

2.  Set permissions for the _/opt/munki-ca_ directory.  This example assumes _munki-enrollment-server_ is the system account under which the MES is running.  (Note that we're using POSIX ACLs to grant the MES user permission to the Munki CA, but you could use regular POSIX permission bits if desired.  ACLs make it flexible to add access to the Munki CA without the limitations of basic POSIX owner and groups.  For this example they are not strictly required.)
<pre>
# POSIX owner and group:
sudo chown -R root:root /opt/munki-ca
# POSIX permissions:
sudo chmod -R 0755 /opt/munki-ca
sudo chmod -R 0770 /opt/munki-ca/private
# Clear existing POSIX ACLs:
sudo setfacl -R -b -k /opt/munki-ca
# Set POSIX ACL mask (defined in the affirmative):
sudo setfacl -R -m m::rwx /opt/munki-ca
# Add ACL for munki-enrollment-server granting read and execute permission:
sudo setfacl -R -n -m u:munki-enrollment-server:rx /opt/munki-ca
# Copy ACLs to default (for inheritance onto newly created children):
sudo getfacl --access /opt/munki-ca | sudo setfacl -R -d -M- /opt/munki-ca
</pre>

3.  Some OpenSSL implementations on various flavors of Linux require that you create a symbolic link from _/etc/CA_ or _/etc/pki/CA_ to your Munki CA directory.  For example:
<pre>
sudo mv /etc/pki/CA /etc/pki/CA.moved
sudo ln -s /opt/munki-ca /etc/pki/CA
sudo mv /etc/CA /etc/CA.moved
sudo ln -s /opt/munki-ca /etc/CA
</pre>

### Build Munki CA ###
1.  Generate the CA private key. When prompted, supply a strong passphrase.  This is the passpharase for the private key for your Munki CA, which you'll reference in your web server configuration and in the configuration for the MES.  Store it in a secure location which you can reference later.  This example generates a 4096-bit RSA key for the CA.
<pre>
sudo -s
cd /opt/munki-ca
openssl genrsa -aes256 -out private/ca.key.pem 4096
exit
</pre>

2.  Generate the CA certificate. The _openssl_ command is interactive, and you'll specify certificate attributes like country, locale, etc.  For the “Common Name (eg, your name or your server's hostname)” attribute, you can specify any name you wish; a host name per-se isn't generally appropriate here.  Consider using something like _Munki CA_ or _Sample Company Mac Management CA_.
<pre>
sudo -s
cd /opt/munki-ca
openssl req -new -x509 -days 3650 -key private/ca.key.pem -sha256 -extensions v3_ca -out certs/ca.cert.pem
chmod 444 certs/ca.cert.pem
exit
</pre>

