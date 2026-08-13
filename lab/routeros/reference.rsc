# RouterOS 7.23.3
# Known-good manual lab reference configuration
#
/interface ethernet
set [ find default-name=ether4 ] disable-running-check=no name=database
set [ find default-name=ether2 ] disable-running-check=no name=dmz
set [ find default-name=ether1 ] disable-running-check=no
set [ find default-name=ether3 ] disable-running-check=no name=internal
/ip address
add address=10.10.10.1/24 comment="DMZ gateway" interface=dmz network=\
    10.10.10.0
add address=10.10.20.1/24 comment="Internal gateway" interface=internal \
    network=10.10.20.0
add address=10.10.30.1/24 comment="Database gateway" interface=database \
    network=10.10.30.0
/ip dhcp-client
add interface=ether1 name=client1
/ip firewall address-list
add address=10.10.10.0/24 comment=DMZ list=lab-networks
add address=10.10.20.0/24 comment=Internal list=lab-networks
add address=10.10.30.0/24 comment=Database list=lab-networks
/ip firewall filter
add action=accept chain=forward comment="LAB: allow established and related" \
    connection-state=established,related,untracked
add action=drop chain=forward comment="LAB: drop invalid" connection-state=\
    invalid
add action=accept chain=forward comment="LAB: allow DMZ to Internal" \
    dst-address=10.10.20.0/24 src-address=10.10.10.0/24
add action=accept chain=forward comment="LAB: allow Internal to Database" \
    dst-address=10.10.30.0/24 src-address=10.10.20.0/24
add action=drop chain=forward comment="LAB: deny other inter-zone traffic" \
    dst-address-list=lab-networks log=yes log-prefix="LAB-DENY " \
    src-address-list=lab-networks
