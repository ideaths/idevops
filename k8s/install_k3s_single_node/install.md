# install


    curl -sfL https://get.k3s.io | K3S_KUBECONFIG_MODE="644" INSTALL_K3S_EXEC="server --flannel-backend=none --cluster-cidr=192.168.0.0/16 --disable-network-policy --disable=traefik" sh -

    kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/tigera-operator.yaml
    kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/custom-resources.yaml
    echo "alias kubectl='microk8s kubectl'" >> ~/.bashrc
    echo "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml" >> ~/.bashrc
    echo "source <(kubectl completion bash)" >> ~/.bashrc
    echo "alias kgp='kubectl get pod '" >> ~/.bashrc
    echo "alias kgs='kubectl get svc '" >> ~/.bashrc
    echo "alias kgn='kubectl get nodes '" >> ~/.bashrc
    echo "alias kgd='kubectl get deploy '" >> ~/.bashrc
    echo "alias kn='kubectl config set-context --current --namespace '" >> ~/.bashrc
    echo "alias ka='kubectl apply -f '" >> ~/.bashrc
    echo "alias kr='kubectl run --dry-run=client -o yaml --image '" >> ~/.bashrc
    echo "alias kcd='kubectl create deployment --dry-run=client -o yaml --image '" >> ~/.bashrc
    echo "alias k='kubectl '" >> ~/.bashrc
    echo "complete -o default -F __start_kubectl k"  >> ~/.bashrc

    source ~/.bashrc

# uninstall

    sudo /usr/local/bin/k3s-uninstall.sh
    --node-external-ip=
