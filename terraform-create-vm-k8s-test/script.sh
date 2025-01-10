#!/bin/bash
terraform apply -auto-approve -destroy -var "GOVC_URL=vcenter.idevops.io.vn" -var "GOVC_USERNAME=administrator@vsphere.local" -var "GOVC_PASSWORD=123abc@A" -lock=false
terraform apply -auto-approve -var "GOVC_URL=vcenter.idevops.io.vn" -var "GOVC_USERNAME=administrator@vsphere.local" -var "GOVC_PASSWORD=123abc@A" -parallelism=3
terraform plan -var "GOVC_URL=vcenter.idevops.io.vn" -var "GOVC_USERNAME=administrator@vsphere.local" -var "GOVC_PASSWORD=123abc@A"
rm -rf /root/.ssh/known_hosts && ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i ansbile_install_k8s/inventory.ini ansbile_install_k8s/install-kube.yml

ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i ansbile_install_k8s/inventory.ini ansbile_install_k8s/Reset-kube.yml



terraform apply -auto-approve -var "GOVC_URL=vcenter.idevops.io.vn" -var "GOVC_USERNAME=administrator@vsphere.local" -var "GOVC_PASSWORD=123abc@A" -parallelism=3 && sleep 100 && rm -rf /root/.ssh/known_hosts && ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i ansbile_install_k8s/inventory.ini ansbile_install_k8s/install-kube.yml
