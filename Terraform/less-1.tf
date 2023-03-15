terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 1"
}

provider "yandex" {
  token     = "AQAAAAAb92xzAATuwTHYxmPMd0itqo43KKT9cGc"
  cloud_id  = "b1gksdu93mdfr7fjjf1n"
  folder_id = "b1grils362d2sgf4mei9"
  zone      = "ru-central1-a"

}





resource "yandex_compute_instance" "vm-2" {
  #  name                      = "terraform2"
  allow_stopping_for_update = true
  #  count                     = 2
  resources {
    cores  = 2
    memory = 2


  }


  boot_disk {
    initialize_params {
      image_id = "fd862bvmr1fe4q1pimtm"
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet-1.id
    nat       = true
  }

  metadata = {
    user-data = "${file("F:/terraform/project/lesson-1/meta.txt")}"
  }

}

resource "yandex_vpc_network" "network-1" {
  name = "network1"
}

resource "yandex_vpc_subnet" "subnet-1" {
  name           = "subnet1"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.network-1.id
  v4_cidr_blocks = ["192.168.10.0/24"]
}


output "internal_ip_address_vm_2" {
  value = yandex_compute_instance.vm-2.network_interface.0.ip_address
}




output "external_ip_address_vm_2" {
  value = yandex_compute_instance.vm-2.network_interface.0.nat_ip_address
}
