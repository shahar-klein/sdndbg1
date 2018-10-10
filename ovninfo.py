#!/usr/bin/env python3

import argparse
import cmd2
import logging
import os
import prettytable
import sys
import traceback

from ovs.db.custom_index import  IndexEntryClass
from ovsdbapp.backend.ovs_idl import connection
from ovsdbapp.backend.ovs_idl import idlutils
from impl_idl import NGNOvnNbApiIdlImpl, NGNOvnSbApiIdlImpl, NGNOvsdbIdl


DEBUG = False
OVNNB_DB = None
OVNSB_DB = None


def wrapColumn(args, text, width=50, separator=None):
    if args.oneline:
        return text

    # separator takes precdence over width!
    if separator:
        return text.replace(separator, '\n')
    if len(text) > width:
        return '\n'.join([text[:width], text[width:]])
    return text


def _get_port_mac_ip(addresses, dynamic_addresses):
    macs = []
    ips = []
    for address in addresses:
        vals = address.split()
        if vals[0] == "unknown":
            macs.append("unknown")
        elif vals[0] == "router":
            macs.append("router")
            ips.append("router")
        elif vals[0] == "dynamic" or (len(vals) > 1 and vals[1] == "dynamic"):
            mac, ip = dynamic_addresses[0].split()
            macs.append(mac)
            ips.append(ip)
        else:
            macs.append(vals[0])
            ips.append(",".join(vals[1:]))
    return ",".join(macs), ",".join(ips)


def _get_port_info_from_sb(PBIdx, port_name):
    try:
        port_binding = list(OVNSB_DB.idl.index_equal("Port_Binding", "logical_port",
                                                     PBIdx(logical_port=port_name)))
    except idlutils.RowNotFound:
        return None, "--", "--"
    type = None
    tunnel_key = '--'
    hostname = "--"
    if port_binding:
        if port_binding[0].chassis:
            hostname = port_binding[0].chassis[0].hostname
        type = (port_binding[0].type if port_binding[0].type else "vif")
        tunnel_key = port_binding[0].tunnel_key
    return type, tunnel_key, hostname


def _get_rsrc_tunnel_key(DBIdx, rsrc_name):
    try:
        datapath_binding = list(OVNSB_DB.idl.index_equal("Datapath_Binding", "external_ids",
                                                         DBIdx(external_ids=dict(name=rsrc_name))))
    except idlutils.RowNotFound:
        return "--"

    if datapath_binding:
        return datapath_binding[0].tunnel_key
    return "--"


class Ovninfo(cmd2.Cmd):
    prompt = "ovninfo> "

    def __init__(self):
        super(Ovninfo, self).__init__()
        self.hidden_commands.extend(['load', 'alias', 'unalias', 'edit', 'history', 'py',
                                     'pyscript', 'set', 'shell', 'shortcuts'])
        self.prompt = "ovninfo> "
        # try:
        #     del cmd2.Cmd.do_load
        #     del cmd2.Cmd.do_alias
        #     del cmd2.Cmd.do_unalias
        #     del cmd2.Cmd.do_edit
        #     del cmd2.Cmd.do_history
        #     del cmd2.Cmd.do_py
        #     del cmd2.Cmd.do_pyscript
        #     del cmd2.Cmd.do_set
        #     del cmd2.Cmd.do_shell
        #     del cmd2.Cmd.do_shortcuts
        # except AttributeError:
        #     pass

    def _get_pretty_table(self, fields):
        table = prettytable.PrettyTable(fields)
        table.border = True
        table.hrules = prettytable.NONE
        table.vrules = prettytable.NONE
        table.align = 'l'
        return table

    def do_status(self, args):
        """Show OVN NB/SB Status"""
        rec = OVNNB_DB.nb_global()
        self.poutput("NorthBound Sequence Number: {}".format(rec.nb_cfg))
        self.poutput("SouthBound Sequence Number: {}".format(rec.sb_cfg))
        self.poutput("Hypervisor Sequence Number: {}".format(rec.hv_cfg))
        self.poutput("Hypervisor Information")

        fields = ["HOSTNAME", "IP", "NBCFG", "SYSTEMID", "MAPPINGS", "D" ]
        table = self._get_pretty_table(fields)
        for chassis in OVNSB_DB.chassis_list().execute():
            chassis_info = []
            chassis_info.append(chassis.hostname)
            encap = chassis.encaps[0]
            chassis_info.append(encap.ip)
            chassis_info.append(chassis.nb_cfg)
            chassis_info.append(chassis.name)
            chassis_info.append(chassis.external_ids.get("ovn-bridge-mappings", "--"))
            cms_options = chassis.external_ids.get("ovn-cms-options")
            gw_enabled = "-"
            if cms_options and 'ngn-gw-enabled' in cms_options:
                gw_enabled = "D"

            chassis_info.append(gw_enabled)
            table.add_row(chassis_info)
        self.poutput(str(table))

        nLSP = len(OVNNB_DB.tables['Logical_Switch_Port'].rows.values())
        nLRP = len(OVNNB_DB.tables['Logical_Router_Port'].rows.values())
        self.poutput("Total number of Logical ports in NorthBound: {}".format(nLSP + nLRP))
        nLP = len(OVNSB_DB.tables['Port_Binding'].rows.values())
        self.poutput("Total number of Logical ports in SouthBound: {}".format(nLP))

    def do_list(self, args):
        """List all Logical Switches and Routers"""
        fields = ["NAME", "TYPE", "#PORT", "#ACL", "#DNS", "#QOS", "#LB", "#NAT", "#RT", "TKEY"]
        table = self._get_pretty_table(fields)
        DBIdx = IndexEntryClass(OVNSB_DB.idl.tables['Datapath_Binding'])
        for ls in OVNNB_DB.ls_list().execute(check_error=True):
            ls_info = []
            ls_info.append(ls.name)
            ls_info.append("Switch")
            ls_info.append(len(ls.ports))
            ls_info.append(len(ls.acls))
            ls_info.append(len(ls.dns_records))
            ls_info.append(len(ls.qos_rules))
            ls_info.append(len(ls.load_balancer))
            # No NAT and Routes information
            ls_info.extend(["--", "--"])
            ls_info.append(_get_rsrc_tunnel_key(DBIdx, ls.name))
            table.add_row(ls_info)
        for lr in OVNNB_DB.lr_list().execute(check_error=True):
            lr_info = []
            lr_info.append(lr.name)
            lr_info.append("Router")
            lr_info.append(len(lr.ports))
            # no ACL, DNS, QOS information for Router
            lr_info.extend(["--", "--", "--"])
            lr_info.append(len(lr.load_balancer))
            lr_info.append(len(lr.nat))
            lr_info.append(len(lr.static_routes))
            lr_info.append(_get_rsrc_tunnel_key(DBIdx, lr.name))
            table.add_row(lr_info)
        self.poutput(str(table))

    def do_ls(self, args):
        """List Logical Switches"""
        fields = ["NAME", "#PORT", "#ACL", "#DNS", "#QOS", "#LB", "TKEY"]
        table = self._get_pretty_table(fields)
        DBIdx = IndexEntryClass(OVNSB_DB.idl.tables['Datapath_Binding'])
        for ls in OVNNB_DB.ls_list().execute(check_error=True):
            ls_info = []
            ls_info.append(ls.name)
            ls_info.append(len(ls.ports))
            ls_info.append(len(ls.acls))
            ls_info.append(len(ls.dns_records))
            ls_info.append(len(ls.load_balancer))
            ls_info.append(len(ls.qos_rules))
            ls_info.append(_get_rsrc_tunnel_key(DBIdx, ls.name))
            table.add_row(ls_info)
        self.poutput(str(table))

    def do_lr(self, args):
        """List Logical Routers"""
        fields = ["NAME", "#PORT", "#LB", "#NAT", "#RT", "TKEY"]
        table = self._get_pretty_table(fields)
        DBIdx = IndexEntryClass(OVNSB_DB.idl.tables['Datapath_Binding'])
        for lr in OVNNB_DB.lr_list().execute(check_error=True):
            lr_info = []
            lr_info.append(lr.name)
            lr_info.append(len(lr.ports))
            lr_info.append(len(lr.load_balancer))
            lr_info.append(len(lr.nat))
            lr_info.append(len(lr.static_routes))
            lr_info.append(_get_rsrc_tunnel_key(DBIdx, lr.name))
            table.add_row(lr_info)
        self.poutput(str(table))

    port_parser = argparse.ArgumentParser(description="List Logical ports (both router and switch)")
    port_parser.add_argument('resource', nargs='?', help="Name of the switch or router")
    @cmd2.with_argparser(port_parser)
    def do_lp(self, args):
        lr_rsrc_list = []
        ls_rsrc_list = []
        fields = ["NAME", "MACADDR", "IPADDR", "TYPE", "UESD", "KEY", "TAG", "HOSTNAME"]
        table = self._get_pretty_table(fields)
        if args.resource:
            rsrc = OVNNB_DB.ls_get(args.resource).execute(check_error=True)
            if rsrc:
                ls_rsrc_list = [rsrc]
            else:
                rsrc = OVNNB_DB.lr_get(args.resource).execute(check_error=True)
                if rsrc:
                    lr_rsrc_list = [rsrc]
                else:
                    raise Exception("Invalid resource name")
        else:
            ls_rsrc_list = OVNNB_DB.ls_list().execute(check_error=True)
            lr_rsrc_list = OVNNB_DB.lr_list().execute(check_error=True)
        PBIdx = IndexEntryClass(OVNSB_DB.idl.tables['Port_Binding'])
        DBIdx = IndexEntryClass(OVNSB_DB.idl.tables['Datapath_Binding'])
        for rsrc in ls_rsrc_list:
            key = _get_rsrc_tunnel_key(DBIdx, rsrc.name)
            table.add_row([rsrc.name, "--", rsrc.other_config.get("subnet", "--"), "SWITCH",
                             "----", key, "--", "--"])
            for port in OVNNB_DB.lsp_list(rsrc.name).execute(check_error=True):
                mac, ips = _get_port_mac_ip(port.addresses, port.dynamic_addresses)
                type, key, hostname = _get_port_info_from_sb(PBIdx, port.name)

                port_info = []
                port_info.append("|->{}".format(port.name))
                port_info.append(mac)
                port_info.append(ips if ips else "--")
                if not type:
                    type = (port.type if port.type else "--")
                port_info.append(type)
                up = "U" if any(port.up) else "-"
                enabled = "E" if all(port.enabled) else "-"
                secure = "S" if len(port.port_security) != 0 else "-"
                dhcp = "D" if len(port.dhcpv4_options) != 0 else "-"
                port_info.append("%s%s%s%s" % (up, enabled, secure, dhcp))
                port_info.append(key)
                port_info.append(port.tag[0] if port.tag else "--")
                port_info.append(hostname)
                table.add_row(port_info)
        for rsrc in lr_rsrc_list:
            key = _get_rsrc_tunnel_key(DBIdx, rsrc.name)
            table.add_row([rsrc.name, "--", "--", "ROUTER", "----", key, "--", "--"])
            for port in OVNNB_DB.lrp_list(rsrc.name).execute(check_error=True):
                type, key, hostname = _get_port_info_from_sb(PBIdx, port.name)
                port_info = []
                port_info.append("|->{}".format(port.name))
                port_info.append(port.mac)
                port_info.append(port.networks[0])
                port_info.append(type)
                enabled = "E" if all(port.enabled) else "-"
                port_info.append("U%s--" % (enabled))
                port_info.append(key)
                port_info.append("--")
                port_info.append(hostname)
                table.add_row(port_info)
        self.poutput(str(table))


def setup_logging(logging_level):
    LOG_FORMATTER_STR = "%(asctime)s %(levelname)s %(name)s - %(message)s"
    l = logging.getLogger()
    l.setLevel(logging_level)
    ch = logging.StreamHandler()
    ch.setLevel(logging_level)
    stdout_formatter = logging.Formatter(LOG_FORMATTER_STR)
    ch.setFormatter(stdout_formatter)
    l.addHandler(ch)


def get_nb_connection(ovnnb_db):
    global  OVNNB_DB
    if OVNNB_DB:
        return OVNNB_DB
    idl = NGNOvsdbIdl.from_server(ovnnb_db, "OVN_Northbound")
    OVNNB_DB = NGNOvnNbApiIdlImpl(connection.Connection(idl, 30))
    return OVNNB_DB


def extract_extid_name(dp_binding):
    return dp_binding.external_ids.get("name")


def get_sb_connection(ovnsb_db):
    global OVNSB_DB
    if OVNSB_DB:
        return OVNSB_DB
    idl = NGNOvsdbIdl.from_server_select_tables(ovnsb_db, "OVN_Southbound",
                                                ["Chassis", "Port_Binding", "Datapath_Binding", "Encap"])
    pb_index = idl.index_create("Port_Binding", "logical_port")
    pb_index.add_column("logical_port")

    db_index = idl.index_create("Datapath_Binding", "external_ids")
    db_index.add_column("external_ids", key=extract_extid_name)
    OVNSB_DB = NGNOvnSbApiIdlImpl(connection.Connection(idl, 30))
    return OVNSB_DB


class CustomHelpAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
        help_output = """
    usage: ovninfo -h
           ovninfo help <subcommand>
           ovninfo [-d] <subcommand>

    ovninfo without any arguments ends up in an interactive shell where one can type
    any of the following subcommands one at a time.

    Global arguments:
      -h, --help            show this help message and exit
      -d, --debug           enable client side debugging

    Subcommands:
        status
        list
        lp
        ls
        lr
        """
        print(help_output)
        parser.exit()


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help', action=CustomHelpAction,
                        help="show this help message and exit")
    parser.add_argument('-d', '--debug', action='store_true', help="enable client side debugging")
    args, unknown_args = parser.parse_known_args()

    logging_level = logging.INFO
    if args.debug:
        global DEBUG
        logging_level = logging.DEBUG
        DEBUG = True
    setup_logging(logging_level)
    ovnnb_db = os.getenv("OVN_NB_DB", "unix:/var/run/openvswitch/ovnnb_db.sock")
    ovnsb_db = os.getenv("OVN_SB_DB", "unix:/var/run/openvswitch/ovnsb_db.sock")
    get_nb_connection(ovnnb_db)
    get_sb_connection(ovnsb_db)

    if unknown_args:
        unknown_args = [" ".join(unknown_args), "quit"]

    # skip past the arguments that we have already parsed
    sys.argv = sys.argv[:1] + unknown_args

    app = Ovninfo()
    app.cmdloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write("Failed operation.\n(%s)\n" % (str(e)))
        if DEBUG:
            sys.stderr.write("at %s" % (traceback.format_exc()))
        sys.exit(1)