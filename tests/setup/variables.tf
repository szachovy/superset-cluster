variable "gateway" {
  description = "Network gateway for the container nodes"
  type        = string
  default     = "172.18.0.1"
}

variable "node_prefix" {
  description = "Prefix of the container nodes"
  type        = string
  default     = "node"
}

variable "node_version" {
  description = "Version of the container nodes deployed"
  type        = string
  default     = "1.0"
}

variable "subnet" {
  description = "Network subnet for the container nodes"
  type        = string
  default     = "172.18.0.0/16"
}
