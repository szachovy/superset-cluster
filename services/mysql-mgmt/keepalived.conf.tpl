
global_defs {
    vrrp_startup_delay 15
    log_file "/opt/default/mysql_router/log/keepalived.log"
    enable_traps
}

vrrp_script status {
    script "/bin/killall -0 mysqlrouter"
    interval 1
    weight 2
}

vrrp_instance virtual_instance {
    state "${STATE}"
    interface "${VIRTUAL_NETWORK_INTERFACE}"
    virtual_router_id 51
    priority ${PRIORITY}
    advert_int 1
    nopreempt
    garp_master_delay 2
    track_script {
        status
    }
    track_interface {
        "${VIRTUAL_NETWORK_INTERFACE}"
    }
    virtual_ipaddress {
        "${VIRTUAL_IP_ADDRESS}/${VIRTUAL_NETWORK_MASK}"
    }
    virtual_routes {
        "${VIRTUAL_NETWORK}" src "${VIRTUAL_IP_ADDRESS}" metric 1 dev "${VIRTUAL_NETWORK_INTERFACE}" scope link
    }
}
