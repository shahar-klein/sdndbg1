"""Custom OVN NB commands.

The ovsdbapp python module doesn't implement all permutations of the
OVN Northbound commands. In this module, we have written additional
commands that are requried to implement NGN's OVN topology.

In certain cases, to meet our needs, we had to inherit the upstream's
implementation to override certain methods (mostly post_commit() and
pre_commit() methods).
"""

from ovsdbapp.backend.ovs_idl import command as basecmd
from ovsdbapp.backend.ovs_idl import rowview
from ovsdbapp.schema.ovn_northbound import commands as cmd

class LrpListCommand(cmd.LrpListCommand):

    def run_idl(self, txn):
        if self.router:
            ports = self.api.lookup('Logical_Router', self.router).ports
        else:
            ports = self.api.tables['Logical_Router_Port'].rows.values()
        self.result = [rowview.RowView(r) for r in ports]


class AddDHCPOptionsCommand(basecmd.BaseCommand):
    def __init__(self, api, cidr, may_exist=False, **columns):
        super(AddDHCPOptionsCommand, self).__init__(api)
        self.cidr = cidr
        self.columns = columns
        self.may_exist = may_exist
        self.new_insert = False

    def _get_dhcp_options_row(self):
        for row in self.api._tables['DHCP_Options'].rows.values():
            ext_ids = getattr(row, 'external_ids', {})
            old_ngn_subnet_id = ext_ids.get('ngn:subnet_uuid')
            ext_ids = self.columns.get('external_ids', {})
            new_ngn_subnet_id = ext_ids.get('ngn:subnet_uuid')
            if (old_ngn_subnet_id and new_ngn_subnet_id and
                    old_ngn_subnet_id == new_ngn_subnet_id):
                return row

    def run_idl(self, txn):
        row = None
        if self.may_exist:
            row = self._get_dhcp_options_row()

        if not row:
            row = txn.insert(self.api._tables['DHCP_Options'])
            self.new_insert = True
        setattr(row, "cidr", self.cidr)
        for col, val in self.columns.items():
            setattr(row, col, val)
        self.result = row.uuid

    def post_commit(self, txn):
        # Update the result with inserted uuid for new inserted row, or the
        # uuid get in run_idl should be real uuid already.
        if self.new_insert:
            self.result = txn.get_insert_uuid(self.result)


class LspAddDHCPOptionsCommand(basecmd.BaseCommand):
    def __init__(self, api, switch_port, cidr, may_exist=False, **columns):
        super(LspAddDHCPOptionsCommand, self).__init__(api)
        self.switch_port = switch_port
        self.cidr = cidr
        self.columns = columns
        self.may_exist = may_exist
        self.new_insert = False

    def _get_dhcp_options_row(self):
        for row in self.api._tables['DHCP_Options'].rows.values():
            ext_ids = getattr(row, 'external_ids', {})
            old_ngn_instance_id = ext_ids.get('ngn:instance_id')
            ext_ids = self.columns.get('external_ids', {})
            new_ngn_instance_id = ext_ids.get('ngn:instance_id')
            if (old_ngn_instance_id and new_ngn_instance_id and
                    old_ngn_instance_id == new_ngn_instance_id):
                return row

    def run_idl(self, txn):
        lsp = self.api.lookup('Logical_Switch_Port', self.switch_port)
        row = None
        if self.may_exist:
            row = self._get_dhcp_options_row()

        if not row:
            row = txn.insert(self.api._tables['DHCP_Options'])
            self.new_insert = True
        setattr(row, "cidr", self.cidr)
        for col, val in self.columns.items():
            setattr(row, col, val)
        if self.new_insert:
            lsp.addvalue('dhcpv4_options', row)
        self.result = row.uuid

    def post_commit(self, txn):
        # Update the result with inserted uuid for new inserted row, or the
        # uuid get in run_idl should be real uuid already.
        if self.new_insert:
            self.result = txn.get_insert_uuid(self.result)


class LsAddCommand(cmd.LsAddCommand):
    def post_commit(self, txn):
        real_uuid = txn.get_insert_uuid(self.result)
        if real_uuid:
            row = self.api.tables[self.table_name].rows[real_uuid]
            self.result = rowview.RowView(row)


class LspAddCommand(cmd.LspAddCommand):
    def post_commit(self, txn):
        real_uuid = txn.get_insert_uuid(self.result)
        if real_uuid:
            row = self.api.tables[self.table_name].rows[real_uuid]
            self.result = rowview.RowView(row)


class AclAddCommand(cmd.AclAddCommand):
    def run_idl(self, txn):
        ls = self.api.lookup('Logical_Switch', self.switch)
        acl = txn.insert(self.api.tables[self.table_name])
        acl.direction = self.direction
        acl.priority = self.priority
        acl.match = self.match
        acl.action = self.action
        acl.log = self.log
        ls.addvalue('acls', acl)
        for col, value in self.external_ids.items():
            acl.setkey('external_ids', col, value)
        self.result = acl.uuid

    def post_commit(self, txn):
        real_uuid = txn.get_insert_uuid(self.result)
        if real_uuid:
            row = self.api.tables[self.table_name].rows[real_uuid]
            self.result = rowview.RowView(row)


class LrNatAddCommand(cmd.LrNatAddCommand):
    def run_idl(self, txn):
        lr = self.api.lookup('Logical_Router', self.router)
        if self.logical_port:
            lp = self.api.lookup('Logical_Switch_Port', self.logical_port)
        nat = txn.insert(self.api.tables['NAT'])
        nat.type = self.nat_type
        nat.external_ip = self.external_ip
        nat.logical_ip = self.logical_ip
        if self.logical_port:
            # It seems kind of weird that ovn uses a name string instead of
            # a ref to a LSP, especially when ovn-nbctl looks the value up by
            # either name or uuid (and discards the result and store the name).
            nat.logical_port = lp.name
            nat.external_mac = self.external_mac
        lr.addvalue('nat', nat)
        self.result = nat.uuid


class LrGWChassisAddCommand(basecmd.BaseCommand):
    def __init__(self, api, router_port, chassis_name, priority, name=None, may_exist=False, **columns):
        if not (priority >= 0 and priority <= 32767):
            raise TypeError("priority not within the valid range")
        super(LrGWChassisAddCommand, self).__init__(api)
        self.router_port = router_port
        self.chassis_name = chassis_name
        if not name:
            self.name = '{0}-{1}'.format(router_port, chassis_name)
        self.priority = priority
        self.columns = columns
        self.may_exist = may_exist

    def run_idl(self, txn):
        lrp = self.api.lookup('Logical_Router_Port', self.router_port)
        # TODO(gmoodalbail): Should I check for duplicate entries here?
        gw_chassis = txn.insert(self.api.tables['Gateway_Chassis'])
        gw_chassis.name = self.name
        gw_chassis.priority = self.priority
        gw_chassis.chassis_name = self.chassis_name
        for col, val in self.columns.items():
            setattr(gw_chassis, col, val)
        lrp.addvalue('gateway_chassis', gw_chassis)
        self.result = gw_chassis.uuid

    def post_commit(self, txn):
        real_uuid = txn.get_insert_uuid(self.result)
        if real_uuid:
            row = self.api.tables['Gateway_Chassis'].rows[real_uuid]
            self.result = rowview.RowView(row)


class LrRouteAddCommand(cmd.LrRouteAddCommand):
    def run_idl(self, txn):
        lr = self.api.lookup('Logical_Router', self.router)
        route = txn.insert(self.api.tables['Logical_Router_Static_Route'])
        route.ip_prefix = self.prefix
        route.nexthop = self.nexthop
        route.policy = self.policy
        if self.port:
            route.output_port = self.port
        lr.addvalue('static_routes', route)
        self.result = route.uuid


class LrpGetNetworksCommand(basecmd.BaseCommand):
    def __init__(self, api, port):
        super(LrpGetNetworksCommand, self).__init__(api)
        self.port = port

    def run_idl(self, txn):
        lrp = self.api.lookup('Logical_Router_Port', self.port)
        self.result = lrp.networks


class LrpGetCommand(basecmd.BaseGetRowCommand):
    table = 'Logical_Router_Port'


class LrGetCommand(basecmd.BaseGetRowCommand):
    table = 'Logical_Router'


class PbGetCommand(basecmd.BaseGetRowCommand):
    table = 'Port_Binding'


class ChassisGetCommand(basecmd.BaseGetRowCommand):
    table = 'Chassis'