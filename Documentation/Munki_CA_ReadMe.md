Certificate Authority Requirement
----------
The MES requires access to a local CA infrastructure, namely a certificate and private key for the enrollment CA, to be installed on the same server as the MES.

This document describes a simple method to create a local CA on RHEL Linux which you can deploy to the MES server(s).  Alternatively, you can create CA materials yourself and move them to the MES server.

For simplicity, this document describes using one Munki CA to:
   - Vend client certificates and keys, and
   - Configure HTTPS for the Munki repo with a server certificate
   
The setup also is geared towards using _nginx_ as both:
   - a reverse proxy for the MES
   - the Munki web repository (via HTTPS)

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
# Follow prompts for attributes.
chmod 444 certs/ca.cert.pem
exit
</pre>

### Build Server Certificate & Key ###
The server's certificate and private key are used for its web server configuration.  For examples here, we recommend _nginx_ for the Munki repository web server.  It also serves as the reverse proxy in front of the MES.

**Important**: You should create a DNS CNAME (alias) record for your Munki server(s).  Even if you have just one server, a CNAME will make migration easier.  It also means that:
   - the CN value of the server's certificate can be the same across all your servers
   - the same server certificate and private key can be used on all of the Munki repo and MES servers
   - the same _nginx_ web server configuration can be used on all of the Munki repo and MES servers
   
For this example, we use **munki.sample.org** as the CNAME for the Munki and MES server(s).

1.  Generate the server private key. When prompted, supply a **temporary** passphrase.  For the server key, we'll remove this passphrase so that you can start and stop the web server (e.g. _nginx_) without having to enter its passphrase every time.
<pre>
sudo -s
SERVER_CNAME=munki.sample.org
cd /opt/munki-ca
# Generate key with passphrase:
openssl genrsa -aes256 -out private/"$SERVER_CNAME".key.with-pass.pem 4096
# Remove passphrase:
openssl rsa -in private/"$SERVER_CNAME".key.with-pass.pem -out private/"$SERVER_CNAME".key.pem
rm private/"$SERVER_CNAME".key.with-pass.pem
exit
</pre>

2.  Generate the server certificate signing request. As before, the _openssl_ command is interactive, and you'll specify certificate attributes like country, locale, etc.  For the “Common Name (eg, your name or your server's hostname)” attribute, specify the CNAME (**munki.sample.org** in this example).
<pre>
sudo -s
SERVER_CNAME=munki.sample.org
cd /opt/munki-ca
openssl req -new -days 3650 -key private/"$SERVER_CNAME".key.pem -sha256 -out certs/"$SERVER_CNAME".csr.pem
# Follow prompts for attributes.
exit
</pre>

3.  Sign the server certificate signing request with the private key of the Munki CA to produce the server certificate for _munki.sample.org_. You will be prompted to enter the private key passphrase for the Munki CA.
<pre>
sudo -s
SERVER_CNAME=munki.sample.org
cd /opt/munki-ca
openssl ca -keyfile private/ca.key.pem -cert certs/ca.cert.pem -extensions usr_cert -notext -md sha256 -in certs/"$SERVER_CNAME".csr.pem -out certs/"$SERVER_CNAME".cert.pem -days 3650
...output omitted...
Sign the certificate? [y/n]:y
1 out of 1 certificate requests certified, commit? [y/n]y
chmod 444 certs/"$SERVER_CNAME".cert.pem 
exit
</pre>
