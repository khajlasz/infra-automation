resource "routeros_interface_ethernet" "dmz" {
  name         = "dmz"
  factory_name = "ether1"
}

resource "routeros_interface_ethernet" "internal" {
  name         = "internal"
  factory_name = "ether2"
}

resource "routeros_interface_ethernet" "database" {
  name         = "database"
  factory_name = "ether3"
}

resource "routeros_interface_ethernet" "observability" {
  name         = "observability"
  factory_name = "ether4"
}

resource "routeros_ip_address" "dmz_gateway" {
  address   = "10.10.10.1/24"
  interface = "dmz"
  comment   = "DMZ gateway"
}

resource "routeros_ip_address" "internal_gateway" {
  address   = "10.10.20.1/24"
  interface = "internal"
  comment   = "Internal gateway"
}

resource "routeros_ip_address" "database_gateway" {
  address   = "10.10.30.1/24"
  interface = "database"
  comment   = "Database gateway"
}

resource "routeros_ip_address" "observability_gateway" {
  address   = "10.10.40.1/24"
  interface = "observability"
  comment   = "Observability gateway"
}

resource "routeros_ip_firewall_addr_list" "dmz" {
  list    = "lab-networks"
  address = "10.10.10.0/24"
  comment = "DMZ"
}

resource "routeros_ip_firewall_addr_list" "internal" {
  list    = "lab-networks"
  address = "10.10.20.0/24"
  comment = "Internal"
}

resource "routeros_ip_firewall_addr_list" "database" {
  list    = "lab-networks"
  address = "10.10.30.0/24"
  comment = "Database"
}

resource "routeros_ip_firewall_addr_list" "observability" {
  list    = "lab-networks"
  address = "10.10.40.0/24"
  comment = "Observability"
}

resource "routeros_ip_firewall_filter" "allow_established_related" {
  chain            = "forward"
  action           = "accept"
  connection_state = "established,related,untracked"
  comment          = "LAB: allow established and related"
}

resource "routeros_ip_firewall_filter" "drop_invalid" {
  chain            = "forward"
  action           = "drop"
  connection_state = "invalid"
  comment          = "LAB: drop invalid"
}

resource "routeros_ip_firewall_filter" "allow_dmz_to_internal" {
  chain       = "forward"
  action      = "accept"
  src_address = "10.10.10.0/24"
  dst_address = "10.10.20.0/24"
  comment     = "Allow DMZ traffic to Internal network"
}

resource "routeros_ip_firewall_filter" "allow_internal_to_database" {
  chain       = "forward"
  action      = "accept"
  src_address = "10.10.20.0/24"
  dst_address = "10.10.30.0/24"
  comment     = "Allow Internal traffic to Database network"
}

resource "routeros_ip_firewall_filter" "allow_metrics_observability_to_internal" {
  chain        = "forward"
  action       = "accept"
  src_address  = "10.10.40.0/24"
  dst_address  = "10.10.20.0/24"
  protocol     = "tcp"
  dst_port     = "9090"
  place_before = routeros_ip_firewall_filter.deny_other_interzone.id
  comment      = "Allow metrics access from Observability to Internal"
}

resource "routeros_ip_firewall_filter" "deny_other_interzone" {
  chain            = "forward"
  action           = "drop"
  src_address_list = "lab-networks"
  dst_address_list = "lab-networks"
  log              = true
  log_prefix       = "LAB-DENY "
  comment          = "LAB: deny other inter-zone traffic"
}
