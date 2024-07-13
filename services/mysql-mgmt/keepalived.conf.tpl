vrrp_script status {
    script "/bin/killall -0 mysqlrouter"
    interval 2
    weight 2
}

vrrp_instance virtual_instance {
    state ${STATE}
    interface ${NETWORK_INTERFACE}
    virtual_router_id 51
    priority ${PRIORITY}
    advert_int 1
    track_script {
        status
    }
    virtual_ipaddress {
        ${VIRTUAL_IP_ADDRESS}
    }
}
