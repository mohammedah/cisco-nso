# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service


# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')
        self.dc_name= service.dc
        self.dc_cz= service.cz
        self.vars= ncs.template.Variables()
        template = ncs.template.Template(service)
        leaf_switches= set(service.primary_leaf)
        leaf_switches= list(leaf_switches)
        self.cz_topology= root.us_datacenters.dc[self.dc_name].l3cz_topology[self.dc_cz]
        spine_as= service.spine_as
        self.all_subnets= []
        for lswitch in leaf_switches:
            leafname= lswitch.name
            leaf_as= lswitch.as_number
            peername= lswitch.peer_leaf
            ibgp_sub= lswitch.ibgp_subnet
            data_subnets= lswitch.leaf_subnets
            ibgp_ips= self.peer_ips(ibgp_sub)
            primary_vlan6= ibgp_ips[0]
            peer_vlan6= ibgp_ips[1]
            ibgp_prefix= ibgp_ips[2]
            primary_loopback0= lswitch.primary_loopback0.split("/")[0]
            peer_loopback0= lswitch.peer_loopback0.split("/")[0]
            self.all_subnets.append(lswitch.primary_loopback0)
            self.all_subnets.append(ibgp_sub)
            self.vars.add('leafname', leafname)
            self.vars.add('peername', peername)
            self.vars.add('leaf_as', leaf_as)
            self.vars.add('peer_vlan6', peer_vlan6)
            self.vars.add('spine_as', spine_as)
            self.vars.add('leaf_loopback0', primary_loopback0)
            self.uplinks(leafname)
            for subnet in data_subnets:
                self.all_subnets.append(subnet)
            print(self.all_subnets)
            self.bgp_subnets(self.all_subnets)
            template.apply('dcrouting-template', self.vars)

            #peer_leaf config.
            self.vars= ncs.template.Variables()
            self.all_subnets= []
            self.all_subnets.append(lswitch.peer_loopback0)
            self.all_subnets.append(ibgp_sub)
            self.vars.add('leafname', peername)
            self.vars.add('peername', leafname)
            self.vars.add('leaf_as', leaf_as)
            self.vars.add('peer_vlan6', primary_vlan6)
            self.vars.add('spine_as', spine_as)
            self.vars.add('leaf_loopback0', peer_loopback0)
            self.uplinks(peername)
            for subnet in data_subnets:
                self.all_subnets.append(subnet)
            print(self.all_subnets)
            self.bgp_subnets(self.all_subnets)
            template = ncs.template.Template(service)
            template.apply('dcrouting-template', self.vars)

    def bgp_subnets(self, subnetlist):
        seq_no= 5
        for subnet in subnetlist:
            self.vars.add('seq_no', seq_no)
            self.vars.add('leaf_subnet', subnet)
            seq_no= seq_no + 5
        print(seq_no)

    def peer_ips(self, subnet):
        ibgp_subnet_info= []
        ip, prefix= subnet.split("/")
        ibgp_subnet_info.append(ip)
        octets= ip.split(".")
        fourth_octet= str(int(octets[3])+1)
        peer_ip= octets[0]+'.'+octets[1]+'.'+octets[2]+'.'+fourth_octet
        ibgp_subnet_info.append(peer_ip)
        ibgp_subnet_info.append(prefix)
        return ibgp_subnet_info

    def uplinks(self, switchname):
        links= self.cz_topology.connections.leaf_sw[switchname].uplinks
        for link in links:
            self.vars.add('leaf_interf', link.leaf_interface )
            self.vars.add('spinename', link.spine_sw)
            self.vars.add('spine_interf', link.spine_interface)
            self.all_subnets.append(link.uplink_subnet)
            link_subnet= self.peer_ips(link.uplink_subnet)
            self.vars.add('leaf_ip', link_subnet[1])
            self.vars.add('prefix', link_subnet[2])
            self.vars.add('spine_ip', link_subnet[0])




#*************************************************
#        vars = ncs.template.Variables()
#        vars.add('DUMMY', '127.0.0.1')
#        template = ncs.template.Template(service)
#        template.apply('dcrouting-template', vars)

    # The pre_modification() and post_modification() callbacks are optional,
    # and are invoked outside FASTMAP. pre_modification() is invoked before
    # create, update, or delete of the service, as indicated by the enum
    # ncs_service_operation op parameter. Conversely
    # post_modification() is invoked after create, update, or delete
    # of the service. These functions can be useful e.g. for
    # allocations that should be stored and existing also when the
    # service instance is removed.

    # @Service.pre_lock_create
    # def cb_pre_lock_create(self, tctx, root, service, proplist):
    #     self.log.info('Service plcreate(service=', service._path, ')')

    # @Service.pre_modification
    # def cb_pre_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')

    # @Service.post_modification
    # def cb_post_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('dcrouting-servicepoint', ServiceCallbacks)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
