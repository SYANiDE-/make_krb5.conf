# make_krb5.conf
Simple tool for quickly mocking up a krb5.conf.  Automate the tedium and monotony out of your workflows like it's annoying, because we all know it is.

## Example workflow
Typically, for kerberos-related activiy, you'll:
  1. enumerate the network
  2. modify your /etc/hosts with entries
  3. make updates to /etc/krb5.conf
  4. make updates to /etc/resolv.conf (protip)
  5. Do your KRB5CCNAME business, whether exported or inline.
  5. Socks proxy and proxychains, or ligolo like an absolute 21st century savage

This repo can help with at least the first four.


## Example workflow in action
Generate your /etc/hosts based on your target environment.  You can quickly enumerate a CIDR range for hosts AND generate a hosts file (at least the contents of interest) with `netexec`, proto `SMB`, the `target subnet CIDR`, and the `--generate-hosts-file [somefile]` flag (behavior of which is to create a file if it doesn't exist, or append to an existing file if it does):
```
──(notroot㉿elysium)-[(master) ~/engagement]
└─$ netexec smb 172.16.210.0/24 --generate-hosts-file hosttemp3
SMB         172.16.210.3    445    DC02             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC02) (domain:dev.TEDIUM.local) (signing:True) (SMBv1:False) 
SMB         172.16.210.99   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:TEDIUM.local) (signing:True) (SMBv1:False) 
Running nxc against 256 targets ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00

┌──(notroot㉿elysium)-[(master) ~/engagement]
└─$ cat hosttemp3 
172.16.210.3     DC02.dev.TEDIUM.local dev.TEDIUM.local DC02
172.16.210.99     DC01.TEDIUM.local TEDIUM.local DC01
```

## Generate a krb5.conf preview

Based on the above hosts file material, quickly generate an /etc/krb5.conf.  

The domain FQDN of the first DC provided in `--dcfqdns` will serve as the libdefaults::default_realm.  

Multiple domain controllers (each with a unique domain) can be added as a comma-separate list of domain controllers, each DC domain will get added as a separate realms:: and domain_realm:: definition(s):
```
┌──(notroot㉿elysium)-[(master) ~/engagement]
└─$ make_krb5.conf.py -d dc02.dev.TEDIUM.local,dc01.TEDIUM.local
[logging]
kdc = FILE:/var/log/krb5_kdc.log
admin-server = FILE:/var/log/krb5_admin-server.log
default = FILE:/var/log/krb5_default.log

[libdefaults]
        default_realm = DEV.TEDIUM.LOCAL
        dns_lookup_realm = false
        dns_lookup_kdc = false
        # dns_uri_lookup = false  ## use this when trying to troubleshoot
# The following krb5.conf variables are only for MIT Kerberos.
        kdc_timesync = 1
        ccache_type = 4
        forwardable = true
        proxiable = true
        rdns = false
# The following libdefaults parameters are only for Heimdal Kerberos.
        fcc-mit-ticketflags = true

[realms]
    DEV.TEDIUM.LOCAL = {
        kdc = DC02.DEV.TEDIUM.LOCAL
        admin_server = DC02.DEV.TEDIUM.LOCAL
        password_server = DC02.DEV.TEDIUM.LOCAL
        default_domain = DEV.TEDIUM.LOCAL
    }        
    TEDIUM.LOCAL = {
        kdc = DC01.TEDIUM.LOCAL
        admin_server = DC01.TEDIUM.LOCAL
        password_server = DC01.TEDIUM.LOCAL
        default_domain = TEDIUM.LOCAL
    }        

[domain_realm]
    dev.tedium.local = DEV.TEDIUM.LOCAL
    .dev.tedium.local = DEV.TEDIUM.LOCAL        
    tedium.local = TEDIUM.LOCAL
    .tedium.local = TEDIUM.LOCAL
```

## Generate a krb5.conf preview and write out to /etc/krb5.conf
Once you are satisfied with the results, you can write it out to /etc/krb5.conf by using sudo, and the script flag `-w`:
```
┌──(notroot㉿elysium)-[(master) ~/engagement]
└─$ sudo make_krb5.conf.py -d dc02.dev.TEDIUM.local,dc01.TEDIUM.local -w
[sudo] password for notroot: 
[logging]
kdc = FILE:/var/log/krb5_kdc.log
admin-server = FILE:/var/log/krb5_admin-server.log
default = FILE:/var/log/krb5_default.log

[libdefaults]
        default_realm = DEV.TEDIUM.LOCAL
        dns_lookup_realm = false
        dns_lookup_kdc = false
        # dns_uri_lookup = false  ## use this when trying to troubleshoot
# The following krb5.conf variables are only for MIT Kerberos.
        kdc_timesync = 1
        ccache_type = 4
        forwardable = true
        proxiable = true
        rdns = false
# The following libdefaults parameters are only for Heimdal Kerberos.
        fcc-mit-ticketflags = true

[realms]
    DEV.TEDIUM.LOCAL = {
        kdc = DC02.DEV.TEDIUM.LOCAL
        admin_server = DC02.DEV.TEDIUM.LOCAL
        password_server = DC02.DEV.TEDIUM.LOCAL
        default_domain = DEV.TEDIUM.LOCAL
    }        
    TEDIUM.LOCAL = {
        kdc = DC01.TEDIUM.LOCAL
        admin_server = DC01.TEDIUM.LOCAL
        password_server = DC01.TEDIUM.LOCAL
        default_domain = TEDIUM.LOCAL
    }        

[domain_realm]
    dev.tedium.local = DEV.TEDIUM.LOCAL
    .dev.tedium.local = DEV.TEDIUM.LOCAL        
    tedium.local = TEDIUM.LOCAL
    .tedium.local = TEDIUM.LOCAL                

[+] Writing /etc/krb5.conf
```

If you don't really want to overwrite your /etc/krb5.conf, you can save the first preview output to a file, and export the KRB5_CONF envar pointing to it (not persistent, only good in current shell):
```
$  tmpfile=$(mktemp)
$  make_krb5.conf.py -d dc02.dev.TEDIUM.local,dc01.TEDIUM.local > $tmpfile
$  export KRB5_CONF=$tmpfile
```

## Workflow BONUS 1

After that, to round out the corners for some outlier tools that don't observe /etc/krb5.conf, edit your /etc/resolv.conf and add your default realm (domain) and the IP of the DC servicing that realm.  

The `/etc/hosts`, `/etc/krb5.conf`, and `/etc/resolv.conf` trifecta is a winning combo for 99% of kerberos-related connectivity/resolution:
```
┌──(notroot㉿elysium)-[(master) ~/htb/academy/adpt/012_Active_Directory_Trust_Attacks]
└─$ cat /etc/resolv.conf
# Generated by NetworkManager
domain dev.TEDIUM.LOCAL  #<-- add
nameserver 172.16.210.3  #<-- add
nameserver 10.0.2.3  #<-- don't remove anything that was there by default, just place it lower priority
```
^^ PROTIP: the "domain" entry should match same case as the krbtgt/dc.DOMAIN.TLD in a generated ticket/ccache.

## Workflow BONUS 2
Ever wish you could quickly get the IP of a host defined in your /etc/hosts file for use inline in a command that only takes IP address?  Well now you can!  Enter the `etchosts.sh`, which does this using `getent` and `awk` commands:
```
## Ref: https://www.geeksforgeeks.org/linux-unix/getent-command-in-linux-with-examples/


The 'getent' command in Linux is a powerful tool that allows users to access entries from various important text files or databases managed by the Name Service Switch (NSS) library. This command is widely used for retrieving user and group information, among other data, stored in databases such as 'passwd', 'group', 'hosts', and more. 'getent' provides a consistent and unified way to query the local files like '/etc/passwd' or network information sources such as LDAP.
```
Common databases queried by getent:
  * 'passwd': Retrieves user account information.
  * 'group': Fetches group account details.
  * 'hosts': Looks up hostnames and IP addresses.
  * 'services': Displays network services and their associated ports.
  * 'protocols': Lists network protocols.
  * 'networks': Retrieves network names.
  * 'shadow': Shows user password information (requires proper permissions).
  * 'aliases': Provides mail alias information.

I wrote a little helper script `etchosts.sh` which uses `getent` with the `ahostsv4` lookup, and uses `awk` to treat the entire output as a single record (essentially, with RS=eof), and return the first IP.  That's on STDOUT.  On STDERR (which evades piping and variable assignment and/or command expansion), a helpful inline message for your engagement documentation for clarity:
Ex.,
```
dc01 == 172.16.210.99  ## `getent ahostsv4 $1 | awk '{print $1}' RS=eof >&1`
```

Usage:
You can use it inline like so:
```
$(etchosts.sh dc01)
```

Example:
```
┌──(notroot㉿elysium)-[(master) ~/engagement]
└─$ certipy find -dc-ip $(etchosts.sh dc01) -u trudy -p Yamah\@momm4\! -stdout -vulnerable
dc01 == 172.16.210.99  ## `getent ahostsv4 $1 | awk '{print $1}' RS=eof >&1`
Certipy v5.0.2 - by Oliver Lyak (ly4k)

[*] Finding certificate templates
[*] Found 33 certificate templates
[*] Finding certificate authorities
[*] Found 1 certificate authority
[*] Found 11 enabled certificate templates
[*] Finding issuance policies
[*] Found 13 issuance policies
[*] Found 0 OIDs linked to templates
[*] Retrieving CA configuration for 'TEDIUM-DC01-CA' via RRP
[!] Failed to connect to remote registry. Service should be starting now. Trying again...
[*] Successfully retrieved CA configuration for 'TEDIUM-DC01-CA'
[*] Checking web enrollment for CA 'TEDIUM-DC01-CA' @ 'DC01.TEDIUM.LOCAL'
[...truncate] 
```


## TODO but I probably won't
Feel free to, but:
  *  Add ability to provide M:1 DCs:domain, not sure if this is needed or in what cases it would be useful.  Probably is.  First iteration of the script was just for quick simplicty, not robustness.
  *  Bring control of krb5.conf options as controllable CLI arguments, I just don't care enough / can edit manually after generation for now.
  * Back up existing krb5.conf, spidey senses tell me this is an important feature to someone.  If you implement, add timestamping in the backup name, would be a real DevSecOp thing to do... just a suggestion.
  * Other?  Make a suggestion, or go it alone and contribute back to the project.  Always looking for improvement ops.  Obviously there's a ton of room 


