# ADD repo
helm repo add bitnami https://charts.bitnami.com/bitnami
# Install rabbitmq cluster operator
helm install rabbitmq-cluster-operator bitnami/rabbitmq-cluster-operator -n rabbitmq-system --create-namespace
kubectl apply -f rabbitmq-cluster.yaml
kubectl apply -f ha-policy.yaml
# Get user/pass
kubectl get secret rabbitmqcluster-prod-default-user -o jsonpath='{.data.username}' | base64 --decode
kubectl get secret rabbitmqcluster-prod-default-user -o jsonpath='{.data.password}' | base64 --decode