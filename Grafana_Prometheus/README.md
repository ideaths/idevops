    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    helm install prometheus prometheus-community/kube-prometheus-stack -n monitor --create-namespace

    helm show values prometheus-community/kube-prometheus-stack > values.yaml
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack -f values.yaml -n monitor
    kubectl apply -k https://github.com/google/cadvisor//deploy/kubernetes/base

    - job_name: "daemonset_cadvisor"
        kubernetes_sd_configs:
        - role: pod
        relabel_configs:
        - source_labels: [__meta_kubernetes_pod_label_app]
          action: keep
          regex: cadvisor
        - action: labelmap
          regex: __meta_kubernetes_pod_label_(.+)
        - source_labels: [__meta_kubernetes_namespace]
          action: replace
          target_label: namespace
        - source_labels: [__meta_kubernetes_pod_name]
          action: replace
          target_label: pod
    - job_name: 'node_exporter'
        scrape_interval: 5s
        static_configs:
        - targets: ['10.9.1.103:9100']
          labels:
            instance: 10.9.1.103
        - targets: ['10.9.1.104:9100']
          labels:
            instance: 10.9.1.104
        - targets: ['10.9.1.105:9100']
          labels:
            instance: 10.9.1.105
        - targets: ['10.9.1.106:9100']
          labels:
            instance: 10.9.1.106
        - targets: ['10.9.1.107:9100']
          labels:
            instance: 10.9.1.107
        - targets: ['10.9.1.108:9100']
          labels:
            instance: 10.9.1.108
        - targets: ['10.9.1.109:9100']
          labels:
            instance: 10.9.1.109
        - targets: ['10.9.1.110:9100']
          labels:
            instance: 10.9.1.110
        - targets: ['10.9.1.150:9100']
          labels:
            instance: 10.9.1.150
        - targets: ['10.9.1.151:9100']
          labels:
            instance: 10.9.1.151
        - targets: ['10.9.1.156:9100']
          labels:
            instance: 10.9.1.156
        - targets: ['10.9.1.157:9100']
          labels:
            instance: 10.9.1.157
        - targets: ['10.9.1.164:9100']
          labels:
            instance: 10.9.1.164
        - targets: ['10.9.1.165:9100']
          labels:
            instance: 10.9.1.165
        - targets: ['10.9.1.166:9100']
          labels:
            instance: 10.9.1.166
        - targets: ['10.9.1.167:9100']
          labels:
            instance: 10.9.1.167
        - targets: ['10.9.1.160:9100']
          labels:
            instance: 10.9.1.160
        - targets: ['10.9.1.161:9100']
          labels:
            instance: 10.9.1.161
        - targets: ['10.9.1.162:9100']
          labels:
            instance: 10.9.1.162
        - targets: ['10.9.1.163:9100']
          labels:
            instance: 10.9.1.163
        - targets: ['10.9.1.169:9100']
          labels:
            instance: 10.9.1.169
        - targets: ['10.9.1.170:9100']
          labels:
            instance: 10.9.1.170
      - job_name: 'windows_node_exporter'
        scrape_interval: 5s
        static_configs:
        - targets: ['10.9.1.101:9182']
          labels:
            instance: 10.9.1.101
        - targets: ['10.9.1.102:9182']
          labels:
            instance: 10.9.1.102
        - targets: ['10.9.1.111:9182']
          labels:
            instance: 10.9.1.111
        - targets: ['10.9.1.112:9182']
          labels:
            instance: 10.9.1.112
        - targets: ['10.9.1.113:9182']
          labels:
            instance: 10.9.1.113
        - targets: ['10.9.1.114:9182']
          labels:
            instance: 10.9.1.114
        - targets: ['10.9.1.132:9182']
          labels:
            instance: 10.9.1.132
