variable "nodes" {
  description = "Number of nodes"
  type        = number
  default     = 5
}

variable "node_version" {
  description = "Version of the container nodes deployed"
  type        = string
  default     = "1.0"
}

variable "node_prefix" {
  description = "Prefix of the container nodes"
  type        = string
  default     = "node"
}

variable "subnet" {
  description = "Network subnet for the container nodes"
  type        = string
  default     = "172.18.0.0/16"
}

variable "gateway" {
  description = "Network gateway for the container nodes"
  type        = string
  default     = "172.18.0.1"
}
