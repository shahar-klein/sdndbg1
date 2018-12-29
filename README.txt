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
help  macro  ovn  ovs  quit

4.2 'ovn' utility:
=======================
sdndbg> ovn
usage: ovn [-h] {trace,ls,status,lr,list,lp,dgp,lrp,lsp,topo} ...

Ovninfo utility for sdndbg

optional arguments:
  -h, --help            show this help message and exit

sub-commands:
  {trace,ls,status,lr,list,lp,dgp,lrp,lsp,topo}
                        Ovninfo utility for sdndbg
    trace               Trace packet flow based on OVN basedLogical Flows
    ls                  List logical switches of ovn
    status              Show OVN’s overall status and chassis info
    lr                  List logical routers of ovn
    list                List logical routers/switches of ovn
    lp                  List Logical ports (both router and switch)
    dgp                 List Distributed gateway ports
    lrp                 Get info of logical router port
    lsp                 Get info of logical switch port
    dgp                 List Distributed gateway ports
    topo                Create graph of logical topology


4.2.1 status' subcommand
========================

sdndbg> ovn status
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

4.2.2 'list' subcommand
======================
sdndbg> ovn list
  NAME                                             TYPE     #PORT   #ACL   #DNS   #QOS   #LB   #NAT   #RT   TKEY
  join-ls-d825566f-c409-4b31-afb3-e9d39dd8671a     Switch   2       0      0      0      0     --     --    3
  ls0                                              Switch   1       0      0      0      0     --     --    6
  dynamic                                          Switch   2       0      0      0      0     --     --    7
  ceph-ls-50b9b5ef-d8c3-406c-9462-6b039752bbd1     Switch   2       0      0      0      0     --     --    2
  ngn-lr-d825566f-c409-4b31-afb3-e9d39dd8671a      Router   1       --     --     --     0     0      3     1
  ceph-lr-d825566f-c409-4b31-afb3-e9d39dd8671a     Router   2       --     --     --     0     0      2     5
  ceph-lrgw-50b9b5ef-d8c3-406c-9462-6b039752bbd1   Router   2       --     --     --     0     0      4     4
sdndbg>

4.2.3 'ls' subcommand
====================

sdndbg> ovn ls
 NAME                                                #PORT   #ACL   #DNS   #QOS   #LB   TKEY   SUBNET          
 ngn-ls-02735523-bff0-4e5a-b085-3f8ea501be16         64      7      0      0      0     397    10.1.0.0/16     
 ngn-ls-6a0449c8-8558-4c65-852f-de4a4e6beb63         3       0      0      0      0     59     10.10.12.0/24   
 ngn-ls-95a6dca4-13db-4c70-9d8c-de8aa006e3ac         64      7      0      0      0     484    10.3.0.0/16     
 ngn-ls-ca52dd93-3f27-4c82-83be-fa0a555c94a9         3       0      0      0      0     58     10.10.11.0/24   
 ngn-ls-097b2c28-a855-4ded-9e97-1f95b9d441d3         63      11     0      0      0     207    10.0.0.0/24     
 ngn-pubgw-ls-20d1b193-b28e-48f8-a095-521156f245c0   4       0      0      0      0     273    8.44.53.128/28  
 ngn-pub-ls-2353ca7a-a0be-4961-95ee-89f965e03fd7     1       12     0      0      0     287    8.44.53.224/29  

4.2.4 'lr' subcommand
=====================

sdndbg> ovn lr
  NAME                                             #PORT   #LB   #NAT   #RT   TKEY
  ngn-lr-d825566f-c409-4b31-afb3-e9d39dd8671a      1       0     0      3     1
  ceph-lr-d825566f-c409-4b31-afb3-e9d39dd8671a     2       0     0      2     5
  ceph-lrgw-50b9b5ef-d8c3-406c-9462-6b039752bbd1   2       0     0      4     4
sdndbg>

4.2.5 'lp' subcommand
====================
sdndbg> ovn lp --help
usage: ovn lp [-h] [-n] [resource]

positional arguments:
  resource    Name of the switch or router

optional arguments:
  -h, --help  show this help message and exit
  -n          Do not resolve hostname

sdndbg> ovn lp
  NAME                                                  MACADDR             IPADDR             TYPE            UESD   KEY   TAG    HOSTNAME
  ngn-pub-ls-aa065c1e-b62f-49a8-954e-8d600c4b4c44       --                  8.44.53.216/29   SWITCH            ----   56    --     --                   
  |->ngn-ltop-aa065c1e-b62f-49a8-954e-8d600c4b4c44      unknown             --               localnet          -E--   1     1112   --                   
  |->ngn-lp-9886095e64af                                98:86:09:5e:64:af   8.44.53.218      vif               UE-D   2     --     nd-sjc3a-c17-dgx-03  
  ngn-lr-0204020b-7425-453e-9c32-273ada149dcd           --                  --               ROUTER            ----   206   --     --                   
  |->ngn-rtos-097b2c28-a855-4ded-9e97-1f95b9d441d3      98:86:09:88:c3:36   10.0.0.1/24      patch             UE--   3     --     --                   
  |->dummy-port                                         00:11:22:33:44:55   192.168.0.1/24   patch             UE--   4     --     --                   
  |->ngn-rtoe-0204020b-7425-453e-9c32-273ada149dcd      98:86:09:97:a2:8d   8.44.53.131/28   patch             UE--   1     --     --                   
  |->cr-ngn-rtoe-0204020b-7425-453e-9c32-273ada149dcd   98:86:09:97:a2:8d   8.44.53.131/28   chassisredirect   UE--   2     --     nd-sjc3a-c17-dgx-01  
  rt-dummy                                              --                  --               ROUTER            ----   3     --     --                   
  ngn-lr-0b33c76d-72be-489b-994b-48ad0d785982           --                  --               ROUTER            ----   5     --     --                   
  ngn-lr-e3e6ea62-7f3f-4fdd-b1e8-2c5f39dbac69           --                  --               ROUTER            ----   57    --     --                   
  |->ngn-rtos-6a0449c8-8558-4c65-852f-de4a4e6beb63      98:86:09:00:d9:c4   10.10.12.1/24    patch             UE--   4     --     --                   
  |->ngn-rtos-ca52dd93-3f27-4c82-83be-fa0a555c94a9      98:86:09:e1:80:ad   10.10.11.1/24    patch             UE--   3     --     --                   
  |->ngn-rtos-fcc0093c-1431-4b92-91e5-f703f845afb5      98:86:09:12:d2:23   10.10.13.1/24    patch             UE--   5     --     --                   
  |->ngn-rtoe-e3e6ea62-7f3f-4fdd-b1e8-2c5f39dbac69      98:86:09:e8:a2:37   8.44.53.133/28   patch             UE--   1     --     --                   
  |->cr-ngn-rtoe-e3e6ea62-7f3f-4fdd-b1e8-2c5f39dbac69   98:86:09:e8:a2:37   8.44.53.133/28   chassisredirect   UE--   2     --     nd-sjc3a-c17-dgx-02  
  ngn-lr-3fe81808-8012-4c3e-bd0d-60023bcc25b1           --                  --               ROUTER            ----   272   --     --                   
  |->ngn-rtos-42b95ba1-78c9-4824-83d4-e96c3638e2f6      98:86:09:90:45:28   10.2.0.1/16      patch             UE--   155   --     --                   
  |->ngn-rtos-02735523-bff0-4e5a-b085-3f8ea501be16      98:86:09:ec:b4:1d   10.1.0.1/16      patch             UE--   117   --     --                   
  |->ngn-rtos-62ded03a-8295-4b03-ac32-caf08b185c0f      98:86:09:f5:d5:b5   10.4.0.1/16      patch             UE--   20    --     --                   
  |->ngn-rtos-95a6dca4-13db-4c70-9d8c-de8aa006e3ac      98:86:09:04:4b:ec   10.3.0.1/16      patch             UE--   204   --     --                   
  |->ngn-rtoe-3fe81808-8012-4c3e-bd0d-60023bcc25b1      98:86:09:fa:d6:05   8.44.53.130/28   patch             UE--   1     --     --                   
  |->cr-ngn-rtoe-3fe81808-8012-4c3e-bd0d-60023bcc25b1   98:86:09:fa:d6:05   8.44.53.130/28   chassisredirect   UE--   2     --     nd-sjc3a-c17-dgx-01
sdndbg>


4.2.6 'ovn trace' subcommand
=======================
sdndbg> ovn trace --help
usage: ovn trace [-h] --from FROM_LPORT [--to TO_LPORT]
                 {ip4,udp,tcp,icmp4,arp,dhcp4} ...

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

sdndbg> ovn trace --from d0 icmp4 --type 8 --code 0 | xargs -I{} ovn-trace dynamic {}

4.2.7 'ovn lsp' subcommand
============================
usage: ovn lsp [-h] [-n] [resource]

positional arguments:
  resource    Name of the switch port

optional arguments:
  -h, --help  show this help message and exit
  -n          Do not resolve hostname

sdndbg> ovn lsp ngn-etor-e3e6ea62-7f3f-4fdd-b1e8-2c5f39dbac69
  NAME                                                MACADDR   IPADDR           TYPE     UESD   KEY   TAG   HOSTNAME  
  ngn-pubgw-ls-20d1b193-b28e-48f8-a095-521156f245c0   --        8.44.53.128/28   SWITCH   ----   273   --    --        
  |->ngn-etor-e3e6ea62-7f3f-4fdd-b1e8-2c5f39dbac69    router    router           patch    UE--   9     --    --    


4.2.8 'ovn lrp' subcommand
==========================    
sdndbg> ovn lrp --help
usage: ovn lrp [-h] [-n] [resource]

positional arguments:
  resource    Name of the router port

optional arguments:
  -h, --help  show this help message and exit
  -n          Do not resolve hostname

sdndbg> ovn lrp ngn-rtos-c5484d90-f072-4190-a310-b6d6bd8616ee 
  NAME                                               MACADDR             IPADDR        TYPE     UESD   KEY   TAG   HOSTNAME  
  ngn-lr-0b33c76d-72be-489b-994b-48ad0d785982        --                  --            ROUTER   ----   5     --    --        
  |->ngn-rtos-c5484d90-f072-4190-a310-b6d6bd8616ee   98:86:09:37:b7:6e   10.0.0.1/24   patch    UE--   1     --    --        


4.2.9 'ovn dgp' subcommand
==========================
sdndbg> ovn dgp --help
usage: ovn dgp [-h] [-n] [resource]

positional arguments:
  resource    Name of the router

optional arguments:
  -h, --help  show this help message and exit
  -n          Do not resolve hostname


sdndbg> ovn dgp
  NAME                                            ROUTER_NAME                                   #GW   ACTIVE_CHASSIS        CHASSIS_LIST              
  ngn-rtoe-0204020b-7425-453e-9c32-273ada149dcd   ngn-lr-0204020b-7425-453e-9c32-273ada149dcd   4     nd-sjc3a-c17-dgx-01   nd-sjc3a-c17-dgx-02(380)  
                                                                                                                            nd-sjc3a-c18-dgx-01(390)  
                                                                                                                            nd-sjc3a-c18-dgx-02(370)  
                                                                                                                            nd-sjc3a-c17-dgx-01(400)  
                                                                                                                                                      
  ngn-rtoe-e3e6ea62-7f3f-4fdd-b1e8-2c5f39dbac69   ngn-lr-e3e6ea62-7f3f-4fdd-b1e8-2c5f39dbac69   4     nd-sjc3a-c17-dgx-02   nd-sjc3a-c17-dgx-02(400)  
                                                                                                                            nd-sjc3a-c18-dgx-02(390)  
                                                                                                                            nd-sjc3a-c18-dgx-01(370)  
                                                                                                                            nd-sjc3a-c17-dgx-01(380)  
                                                                                                                                                      
  ngn-rtoe-3fe81808-8012-4c3e-bd0d-60023bcc25b1   ngn-lr-3fe81808-8012-4c3e-bd0d-60023bcc25b1   2     nd-sjc3a-c17-dgx-01   nd-sjc3a-c18-dgx-01(200)  
                                                                                                                            nd-sjc3a-c17-dgx-01(190)  
                                                                                                                                                      
  ngn-rtoe-e3e6ea62-7f3f-4fdd-b1e8-2c5f39dbac69                                                 4     nd-sjc3a-c17-dgx-02   nd-sjc3a-c17-dgx-02(400)  
                                                                                                                            nd-sjc3a-c18-dgx-02(390)  
                                                                                                                            nd-sjc3a-c18-dgx-01(370)  
                                                                                                                            nd-sjc3a-c17-dgx-01(380)  

4.2.10 'ovn topo' subcommand
============================
sdndbg> ovn topo --help
usage: ovn topo [-h] [-v] [--output OUTPUT] root

positional arguments:
  root             Specify the root of graph

optional arguments:
  -h, --help       show this help message and exit
  -v               Include vm and localnet ports
  --output OUTPUT

sdndbg> ovn topo ngn-ls-02735523-bff0-4e5a-b085-3f8ea501be16 -v

This generates ovn.dot file which could be used to generate ps or pdf.
$dot -Tps ovn.dot -o graph.ps


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


