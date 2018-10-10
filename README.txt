1. Introduction:
================

sdndbg CLI utility provides subcommands using which one could debug OVN logical topologies.
It provides a quick overview of the Logical topology, i.e.,
 -- logical switch ports connection to logical switches
 -- logical router ports connection to logical routers
 -- logical switches connection to logical router (and vice-versa)
 -- Distributed gateway ports info
 -- L3 gateway info
 -- L2 gateway info
 -- Router peering

It combines information from both OVNNB and OVNSB and provides physical information as well.
 -- Is a logical port is bound, and if so, to which port
 -- what is Geneve tunnel ID used for a particular datapth
 -- which host is support distributed gateway port
 -- Is the port administratively enabled?
 -- Is the port eanbled for security

2. Installation:
================
git clone https://gitlab-master.nvidia.com/sdn/sdndbg.git
cd sdndbg
pip install -r requirements.txt
./sdndbg --help

3. Interactive Mode:
=====================
The utility is built using python cmd2 module which is very powerful and provides an interactive
user interface. This is beneficial for several reasons:
-- You connect to OVNSB and OVNDB once and then fetch the whole DB to the client. The subsequent
   commands work off of the client IDL information.
-- You can redirect or pipe the output and use your favorite shell command on it
-- You can directly run shell command without exiting the CLI using '!'
-- In addition to all this there is history, tab-completion, and many more. This is all free for us
   from cmd2 python module. See: https://cmd2.readthedocs.io/en/latest/freefeatures.html

4. Examples:
=============

4.1 Usage:
==========
[girishmg@ngvpn01-169-182:~/git/sdndbg]
>./sdndbg
sdndbg> help

Documented commands (type help <topic>):
========================================
help  list  lp  lr  ls  quit  status  trace

sdndbg> help list
List all Logical Switches and Routers
sdndbg> help lp
usage: lp [-h] [resource]

List Logical ports (both router and switch)

positional arguments:
  resource    Name of the switch or router

optional arguments:
  -h, --help  show this help message and exit
sdndbg> help lr
List Logical Routers
sdndbg> help ls
List Logical Switches
sdndbg> help status
Show OVN NB/SB Status
sdndbg> help trace
usage: trace [-h] --from FROM_LPORT [--to TO_LPORT]
             {ip4,udp,tcp,icmp4,arp,dhcp4} ...

Trace packet flow based on OVNSB Logical Flows

optional arguments:
  -h, --help            show this help message and exit
  --from FROM_LPORT     Specify the source logical port
  --to TO_LPORT         Specify the destination logical port

Subcommands:
  Supported protocols

  {ip4,udp,tcp,icmp4,arp,dhcp4}
    ip4                 Trace IPv4 packet
    udp                 Trace UDP packet
    tcp                 Trace TCP packet
    icmp4               Trace ICMP4 packet
    arp                 Trace ARP packet
    dhcp4               Trace DHCP packet
sdndbg>


4.2 'status' subcommand
========================

sdndbg> status
NorthBound Sequence Number: 1
SouthBound Sequence Number: 1
Hypervisor Sequence Number: 1
Hypervisor Information
  HOSTNAME       IP               NBCFG   SYSTEMID                               MAPPINGS               D
  ubuntuNode3    192.168.13.103   4       655a0495-2149-45f8-bf08-2425765ca0d2                          -
  ubuntuMaster   192.168.13.100   1       86d4f712-484b-4edc-835d-2135fa838782   provider:br-provider   -
  ubuntuNode2    192.168.13.102   4       5e897598-cec4-42e2-89d5-0da9f953a609   provider:br-provider   -
  ubuntuNode1    192.168.13.101   7       38bd4fb0-f822-4407-bcaf-286f4752255d   provider:br-provider   -
Total number of Logical ports in NorthBound: 12
Total number of Logical ports in SouthBound: 12
sdndbg>

sdndbg> status |grep ubuntuNode1
  ubuntuNode1    192.168.13.101   7       38bd4fb0-f822-4407-bcaf-286f4752255d   provider:br-provider   -
sdndbg>

4.3 'list' subcommand
======================
sdndbg> list
  NAME                                             TYPE     #PORT   #ACL   #DNS   #QOS   #LB   #NAT   #RT   TKEY
  join-ls-d825566f-c409-4b31-afb3-e9d39dd8671a     Switch   2       0      0      0      0     --     --    3
  ls0                                              Switch   1       0      0      0      0     --     --    6
  dynamic                                          Switch   2       0      0      0      0     --     --    7
  ceph-ls-50b9b5ef-d8c3-406c-9462-6b039752bbd1     Switch   2       0      0      0      0     --     --    2
  ngn-lr-d825566f-c409-4b31-afb3-e9d39dd8671a      Router   1       --     --     --     0     0      3     1
  ceph-lr-d825566f-c409-4b31-afb3-e9d39dd8671a     Router   2       --     --     --     0     0      2     5
  ceph-lrgw-50b9b5ef-d8c3-406c-9462-6b039752bbd1   Router   2       --     --     --     0     0      4     4
sdndbg>

4.4 'ls' subcommand
====================

sdndbg> ls
  NAME                                           #PORT   #ACL   #DNS   #QOS   #LB   TKEY
  join-ls-d825566f-c409-4b31-afb3-e9d39dd8671a   2       0      0      0      0     3
  ls0                                            1       0      0      0      0     6
  dynamic                                        2       0      0      0      0     7
  ceph-ls-50b9b5ef-d8c3-406c-9462-6b039752bbd1   2       0      0      0      0     2
sdndbg>

4.5 'lr' subcommand
=====================

sdndbg> lr
  NAME                                             #PORT   #LB   #NAT   #RT   TKEY
  ngn-lr-d825566f-c409-4b31-afb3-e9d39dd8671a      1       0     0      3     1
  ceph-lr-d825566f-c409-4b31-afb3-e9d39dd8671a     2       0     0      2     5
  ceph-lrgw-50b9b5ef-d8c3-406c-9462-6b039752bbd1   2       0     0      4     4
sdndbg>

4.6 'lp' subcommand
====================
sdndbg> lp
  NAME                                                MACADDR             IPADDR             TYPE        UESD   KEY   TAG    HOSTNAME
  join-ls-d825566f-c409-4b31-afb3-e9d39dd8671a        --                  --                 SWITCH      ----   3     --     --
  |->ceph-jtog-50b9b5ef-d8c3-406c-9462-6b039752bbd1   00:00:00:53:4D:F0   --                 l3gateway   UE--   1     --     --
  |->ceph-jtor-d825566f-c409-4b31-afb3-e9d39dd8671a   00:00:00:BD:31:D4   --                 patch       UE--   2     --     --
  ls0                                                 --                  --                 SWITCH      ----   6     --     --
  |->ls0_p0                                           00:01:02:03:04:05   192.168.1.14       vif         -E--   1     --     --
  dynamic                                             --                  192.168.192.0/24   SWITCH      ----   7     --     --
  |->d1                                               00:00:01:01:02:03   192.168.192.3      vif         -E--   2     --     --
  |->d0                                               0a:00:00:00:00:01   192.168.192.2      vif         -E--   1     --     --
  ceph-ls-50b9b5ef-d8c3-406c-9462-6b039752bbd1        --                  192.168.1.24/30    SWITCH      ----   2     --     --
  |->ceph-ltop-50b9b5ef-d8c3-406c-9462-6b039752bbd1   unknown             --                 localnet    -E--   1     1222   --
  |->ceph-etor-50b9b5ef-d8c3-406c-9462-6b039752bbd1   00:00:00:3A:17:B9   --                 l3gateway   UE--   2     --     --
  ngn-lr-d825566f-c409-4b31-afb3-e9d39dd8671a         --                  --                 ROUTER      ----   1     --     --
  |->ceph-ntoc-d825566f-c409-4b31-afb3-e9d39dd8671a   00:00:00:a0:9a:57   192.168.14.2/24    patch       UE--   1     --     --
  ceph-lr-d825566f-c409-4b31-afb3-e9d39dd8671a        --                  --                 ROUTER      ----   5     --     --
  |->ceph-cton-d825566f-c409-4b31-afb3-e9d39dd8671a   00:00:00:2a:cb:88   192.168.14.1/24    patch       UE--   1     --     --
  |->ceph-rtoj-d825566f-c409-4b31-afb3-e9d39dd8671a   00:00:00:bd:31:d4   192.168.13.1/24    patch       UE--   2     --     --
  ceph-lrgw-50b9b5ef-d8c3-406c-9462-6b039752bbd1      --                  --                 ROUTER      ----   4     --     --
  |->ceph-gtoj-50b9b5ef-d8c3-406c-9462-6b039752bbd1   00:00:00:53:4d:f0   192.168.13.2/24    l3gateway   UE--   1     --     --
  |->ceph-rtoe-50b9b5ef-d8c3-406c-9462-6b039752bbd1   00:00:00:3a:17:b9   192.168.1.26/30    l3gateway   UE--   2     --     --
sdndbg>

sdndbg> lp dynamic
  NAME      MACADDR             IPADDR             TYPE     UESD   KEY   TAG   HOSTNAME
  dynamic   --                  192.168.192.0/24   SWITCH   ----   7     --    --
  |->d1     00:00:01:01:02:03   192.168.192.3      vif      -E--   2     --    --
  |->d0     0a:00:00:00:00:01   192.168.192.2      vif      -E--   1     --    --
sdndbg>

4.7 'trace' subcommand
=======================
sdndbg> trace --from d0 ip4
'inport == "d0" && eth.src == 0a:00:00:00:00:01 && eth.dst == ff:ff:ff:ff:ff:ff && ip4 && ip4.src == 192.168.192.2 && ip4.dst == 255.255.255.255 && ip.ttl == 32'
sdndbg> trace --from d0 dhcp4
'inport == "d0" && eth.src == 0a:00:00:00:00:01 && eth.dst == ff:ff:ff:ff:ff:ff && ip4 && ip4.src == 192.168.192.2 && ip4.dst == 255.255.255.255 && ip.ttl == 32 && udp && udp.src == 68 && udp.dst == 67'
sdndbg> trace --from d0 tcp --dst 22
'inport == "d0" && eth.src == 0a:00:00:00:00:01 && eth.dst == ff:ff:ff:ff:ff:ff && ip4 && ip4.src == 192.168.192.2 && ip4.dst == 255.255.255.255 && ip.ttl == 32 && tcp && tcp.dst == 22'
sdndbg> trace --from d0 icmp4 --type 8 --code 0
'inport == "d0" && eth.src == 0a:00:00:00:00:01 && eth.dst == ff:ff:ff:ff:ff:ff && ip4 && ip4.src == 192.168.192.2 && ip4.dst == 255.255.255.255 && ip.ttl == 32 && icmp4 && icmp4.type == 8 && icmp4_code == 0'
sdndbg>

*take the output from above and pipe it to ovn-trace*

sdndbg> trace --from d0 icmp4 --type 8 --code 0 | xargs -I{} ovn-trace dynamic {}


5. Non-Interactive Mode:
========================
Run the following for non-interactive mode:
./sdndbg status
./sdndbg list
./sdndbg ls
./sdndbg lr
./sdndbg trace

6. Future work:
===============
-- Raft specific information
-- integrating ofproto/trace from Venu's tool


