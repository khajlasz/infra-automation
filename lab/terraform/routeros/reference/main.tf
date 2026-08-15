terraform {
  required_providers {
    routeros = {
      source  = "terraform-routeros/routeros"
      version = "1.99.1"
    }
  }
}

provider "routeros" {}

resource "routeros_interface_ethernet" "dmz" {
  factory_name = "ether1"
  name         = "dmz"
}

resource "routeros_interface_ethernet" "internal" {
  factory_name = "ether2"
  name         = "internal"
}

resource "routeros_interface_ethernet" "database" {
  factory_name = "ether3"
  name         = "database"
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

resource "routeros_ip_firewall_filter" "allow_dmz_to_internal" {
  chain       = "forward"
  action      = "accept"
  src_address = "10.10.10.0/24"
  dst_address = "10.10.20.0/24"
  comment     = "LAB: allow DMZ to Internal"
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

resource "routeros_ip_firewall_filter" "allow_internal_to_database" {
  chain       = "forward"
  action      = "accept"
  src_address = "10.10.20.0/24"
  dst_address = "10.10.30.0/24"
  comment     = "LAB: allow Internal to Database"
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

