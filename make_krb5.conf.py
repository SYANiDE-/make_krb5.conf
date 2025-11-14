#!/usr/bin/env python3
import os, sys, argparse, configparser

def getargs():
    AP = argparse.ArgumentParser(description="Make entries for /etc/krb5.conf, optionally write a new one")
    AP.add_argument("-d","--dcfqdns",required=True,type=str,default=None,help="Domain Controller(s), comma-separated. First one should be the one to use as default domain")
    AP.add_argument("-w","--write",action='store_true',help="write to /etc/krb5.conf (requires sudo)")
    AR, trash = AP.parse_known_args()
    return vars(AR)

def writer(rendered):
    with open("/etc/krb5.conf","w") as F:
        F.write(rendered)
        F.close()

def formatter(dcs):
    entries = []
    indent=8
    while True:
        nextdc = next(dcs,None)
        if nextdc is None:
            break
        index, dc = nextdc
        kdc_port=dc.split(":")[1] if len(dc.split(":")) > 1 else "88"
        dchost = dc.split(".")[0]
        dcdomain = '.'.join(dc.split(".")[1:])
        dc_lower=dchost.lower()
        dc_upper=dchost.upper()
        domain_lower=dcdomain.lower()
        domain_upper=dcdomain.upper()
        if index == 0:
            default_realm = domain_upper
        entry = "\n".join([x[indent:] for x in f"""\
            {domain_upper} = {{
                kdc = {dc_lower}.{domain_lower}:88
                admin_server = {dc_lower}.{domain_lower}
                password_server = {dc_lower}.{domain_lower}
                default_domain = {domain_lower}
            }}\
        """.split("\n")])
        mapping = "\n".join([x[indent:] for x in f"""\
            {domain_lower} = {domain_upper}
            .{domain_lower} = {domain_upper}\
        """.split("\n")])
        entries.append([entry,mapping])
    return default_realm, entries

def renderer(default_realm,entries):
    indent=8
    entrylist = ('\n'+(" "*indent)).join([('\n'+(" "*indent)).join(y) for y in [x[0].split("\n") for x in entries]])
    mappinglist = ('\n'+(" "*indent)).join([('\n'+(" "*indent)).join(y) for y in [x[1].split("\n") for x in entries]])
    krb5conf = "\n".join([x[indent:] for x in f"""\
        [logging]
        kdc = FILE:/var/log/krb5_kdc.log
        admin-server = FILE:/var/log/krb5_admin-server.log
        default = FILE:/var/log/krb5_default.log

        [libdefaults]
                default_realm = {default_realm}
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
        {entrylist}

        [domain_realm]
        {mappinglist}        
        """.split("\n")])
    print(krb5conf)
    return krb5conf

def main():
    ARGS = getargs()
    dcs = enumerate(ARGS['dcfqdns'].split(","))
    default_realm, entries = formatter(dcs)
    rendered = renderer(default_realm, entries)
    if ARGS['write'] == True:
        print(f"[+] Writing /etc/krb5.conf")
        writer(rendered)

if __name__=="__main__":
    main()
