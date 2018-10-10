import logging
import commands as cmd

from ovsdbapp.backend.ovs_idl import connection
from ovsdbapp.backend.ovs_idl import idlutils
from ovsdbapp.backend.ovs_idl import transaction
from ovsdbapp.schema.ovn_northbound import impl_idl
from ovsdbapp.schema.ovn_southbound import impl_idl as sb_impl_idl

logger = logging.getLogger(__name__)

class NGNOvnNbTransaction(transaction.Transaction):
    def pre_commit(self, txn):
        # self.api.nb_global().increment('nb_cfg')
        pass


class NGNOvnNbApiIdlImpl(impl_idl.OvnNbApiIdlImpl):
    """Custom OVN NB API IDL implementation.

    To realize NGN's OVN topology we needed additional methods in
    upstream's (ovsdbapp) implementation of OVN NB API IDL.
    """

    def __init__(self, connection):
        super(NGNOvnNbApiIdlImpl, self).__init__(connection)

    def create_transaction(self, check_error=False, log_errors=True, timeout=None, **kwargs):
        return NGNOvnNbTransaction(self, self.ovsdb_connection,
                                   timeout if timeout else self.ovsdb_connection.timeout,
                                   check_error, log_errors)

    def nb_global(self):
        return next(iter(self.tables['NB_Global'].rows.values()))

    @property
    def inactivity_probe(self):
        return self.idl._session.reconnect.get_probe_interval()

    @inactivity_probe.setter
    def inactivity_probe(self, probe_interval):
        self.idl._session.reconnect.set_probe_interval(probe_interval)

    def ls_add(self, switch=None, may_exist=False, **columns):
        return cmd.LsAddCommand(self, switch, may_exist, **columns)

    def lsp_add(self, switch, port, parent_name=None, tag=None,
                may_exist=False, **columns):
        return cmd.LspAddCommand(self, switch, port, parent_name, tag,
                                 may_exist, **columns)

    def acl_add(self, switch, direction, priority, match, action, log=False,
                may_exist=False, **external_ids):
        return cmd.AclAddCommand(self, switch, direction, priority,
                                 match, action, log, may_exist, **external_ids)

    def lr_nat_add(self, router, nat_type, external_ip, logical_ip,
                   logical_port=None, external_mac=None, may_exist=False):
        return cmd.LrNatAddCommand(
            self, router, nat_type, external_ip, logical_ip, logical_port,
            external_mac, may_exist)

    def create_dhcp_options(self, cidr, may_exist=False, **columns):
        return cmd.AddDHCPOptionsCommand(self, cidr, may_exist=may_exist, **columns)

    def lr_route_add(self, router, prefix, nexthop, port=None,
                     policy='dst-ip', may_exist=False):
        return cmd.LrRouteAddCommand(self, router, prefix, nexthop, port,
                                     policy, may_exist)

    def lrp_gw_chassis_add(self, router_port, chassis_name, priority, may_exist=False, **columns):
        return cmd.LrGWChassisAddCommand(self, router_port, chassis_name, priority, may_exist, **columns)

    def lrp_get(self, port):
        return cmd.LrpGetCommand(self, port)

    def lr_get(self, router):
        return cmd.LrGetCommand(self, router)

    def lrp_list(self, router=None):
        return cmd.LrpListCommand(self, router)

    def lsp_add_dhcpv4_options(self, switch_port, cidr, may_exist=False, **columns):
        return cmd.LspAddDHCPOptionsCommand(self, switch_port, cidr, may_exist, **columns)

    def get_gw_chassis_nrouters(self, gw_chassis_list):
        """Get the list of gateway chassis and numbers of routers bound to it.

        @param   gw_chassis_list: list of gateway chassis candidate
        @return: list of (chassis_name, nrouters)
        """
        if not gw_chassis_list:
            return []

        chassis_bindings = {}
        for chassis_name in gw_chassis_list:
            chassis_bindings.setdefault(chassis_name, 0)

        # walk through the "Logical Router Port" table to get the list of
        # gateway chassis bound to each logical router port, get the numbers
        # of logical routers associated with each chassis, only count the
        #  highest priority gateway chassis for each logical router port
        for lrp in self.lrp_list().execute(check_error=True):
            if not lrp.name.startswith('ngn-rtoe'):
                continue

            # sort gateway chassis bound to this lrp based on its priority, highest first
            lrp_chlist = [(c.chassis_name, c.priority) for c in lrp.gateway_chassis]
            sorted_list = sorted(lrp_chlist, reverse=True, key=lambda chassis: chassis[1])

            # find the highest priority gw_chassis in the candidate list
            # increase the number of routers bound to this gw_chassis
            for chassis_name, prio in sorted_list:
                if chassis_name not in gw_chassis_list:
                    continue
                chassis_bindings[chassis_name] += 1
                break

        return chassis_bindings.items()


class NGNOvnSbApiIdlImpl(sb_impl_idl.OvnSbApiIdlImpl):
    """Custom OVN SB API IDL implementation.

    To realize NGN's OVN topology we needed additional methods in
    upstream's (ovsdbapp) implementation of OVN SB API IDL.
    """

    _OVN_GATEWAY_ENABLED = "ngn-gw-enabled"
    _OVN_CMS_OPTIONS = "ovn-cms-options"

    @property
    def inactivity_probe(self):
        return self.idl._session.reconnect.get_probe_interval()

    @inactivity_probe.setter
    def inactivity_probe(self, probe_interval):
        self.idl._session.reconnect.set_probe_interval(probe_interval)

    def get_all_gateway_chassis(self):
        """Get the list of gateway chassis.

        @return: list of gateway_chassis_name
        """
        # walk though the Chassis table to find the gateway chassis
        gw_chassis_list = []
        for ch in self.chassis_list().execute(check_error=True):
            cms_options = ch.external_ids.get(self._OVN_CMS_OPTIONS, '')
            if self._OVN_GATEWAY_ENABLED in cms_options.split(','):
                gw_chassis_list.append(ch.name)

        return gw_chassis_list

    def pb_get(self, name):
        return cmd.PbGetCommand(self, name)

    def chassis_get(self, chassis):
        return cmd.ChassisGetCommand(self, chassis)

class NGNOvsdbIdl(connection.OvsdbIdl):
    """
    Custom implementation to replicate select tables of a particular schema from
    remote server.

    It so happens that the caller might be interested in handful of tables instead
    of lot of tables. This implementation provides one such method to subscribe for
    only interested tables.
    """

    @classmethod
    def from_server_select_tables(cls, connection_string, schema_name, tables):
        """Create the Idl instance by pulling the schema from OVSDB server"""
        remotes = connection_string.split(',')
        for remote in remotes:
            try:
                helper = idlutils.get_schema_helper(remote, schema_name)
                for table in tables:
                    helper.register_table(table)
                return cls(connection_string, helper)
            except Exception as e:
                # one of multiple servers is not available, try next one
                logger.debug("connection to {} failed: {}".format(remote, e))
                continue
        raise Exception("Could not connect to any of the remotes %s" % connection_string.split(','))

    @classmethod
    def from_server(cls, connection_string, schema_name):
        """Create the Idl instance by pulling the schema from OVSDB server"""
        remotes = connection_string.split(',')
        for remote in remotes:
            try:
                helper = idlutils.get_schema_helper(remote, schema_name)
                helper.register_all()
                return cls(connection_string, helper)
            except Exception as e:
                # one of multiple servers is not available, try next one
                logger.debug("connection to {} failed: {}".format(remote, e))
                continue
        raise Exception("Could not connect to any of the remotes %s" % connection_string.split(','))

