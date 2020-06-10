#!/usr/bin/env python3

from xml.dom import minidom
import os
import subprocess
import fileinput
import shlex
import time
import logging


# Added Logging

logname = "log.txt"
logging.basicConfig(filename=logname, filemode='a', format='%(levelname)s %(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S', level=logging.DEBUG)
def xmlparser():
    '''
    Parses a vmware tools XML file and returns all properties in a dictionary
    '''
    with open('sample.xml', 'w') as f:
        p1 = subprocess.run(
            'vmtoolsd --cmd "info-get guestinfo.ovfEnv" >> sample.xml', stdout=f, shell=True)
        f.close()
    PROPERTIES = {}
    p = minidom.parse('sample.xml')
    item_list = p.getElementsByTagName('Property')
    for i in item_list:
        key = i.attributes['oe:key'].value
        value = i.attributes['oe:value'].value
        PROPERTIES[key] = value
    return PROPERTIES

def createNetworkProps(parsed_xml):
    network_props = {
        'BOOTPROTO': "BOOTPROTO=static",
        "NETMASK=": f"NETMASK={parsed_xml['onapp.netmask']}",
        "IPADDR=": f"IPADDR={parsed_xml['onapp.ipaddr']}",
        'GATEWAY=': f"GATEWAY={parsed_xml['onapp.gw']}",
        'DNS1=': f'DNS1={parsed_xml["onapp.dns"]}',
    }

    return network_props


def createOnAppProps(parsed_xml):
    try:
        onapp_props = {
            'license_key' : f'{parsed_xml["onapp.license"]}'
        }
        return onapp_props
    except:
        pass


def changer(props,file_to_change):
    """Function to update files in place
    Arguments:
        props {Dictionary} -- Dictionary where key = lookup line string and value = new line value
        file_to_change {Filename} -- Filename to make changes
        Does not output anything , changes are made inside the file
    """

    mylist = list(props.keys())
    for line in fileinput.input(files=(file_to_change), inplace=1):
        for each in mylist:
            if each in line:
                line = f"{props[each]}\n"
            else:
                line = line
        print(line, end='')


def changeHostname(props):
    hostname_cmd = f"hostnamectl set-hostname {props['onapp.fqdn']}"
    x = subprocess.run(hostname_cmd.split(' '))
    
    if x.returncode != 0:
        logging.info("failed to set hostname")
    else:
        return logging.info("Hostname Set")

def reinstall_rabbitmq():
    cmd = "/onapp/onapp-rabbitmq/onapp-cp-rabbitmq.sh"
    run = subprocess.Popen(cmd)
    run.wait()
    return logging.info("Re-installed Rabbit-MQ")


# props = xmlparser()
# print(props)

# net_props = createNetworkProps(xmlparser())

# print(net_props)

# onapp_props = createOnAppProps(xmlparser())
# print(onapp_props)

# reinstall_rabbitmq()

# changeHostname(props)
if (os.path.isfile('step-1') == 0) and (os.path.isfile('step-2') == 0) :
    print("run step-1")
    props = xmlparser()
    print(props)

    net_props = createNetworkProps(xmlparser())
    print(net_props)

    onapp_props = createOnAppProps(xmlparser())
    print(onapp_props)    
    os.system('touch step-1')

    changer(net_props,"/etc/sysconfig/network-scripts/ifcfg-ens160")
    changeHostname(props)
    time.sleep(5)
    logging.info("ran step1")
    os.system("shutdown -r now")
elif (os.path.isfile('step-1') == 1) and (os.path.isfile('step-2') == 0) :
    print("run step-2 update rabbitmq")
    reinstall_rabbitmq()
    os.system('touch step-2')
    logging.info("ran step2")
elif (os.path.isfile('step-1') == 0) and (os.path.isfile('step-2') == 1) :
    print("no step-1")
    logging.info("no step-1")
elif (os.path.isfile('step-1') == 1) and (os.path.isfile('step-2') == 1) :
    print("do nothing")
    logging.info("not needed")


