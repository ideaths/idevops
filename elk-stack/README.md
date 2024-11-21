    helm repo add elastic https://helm.elastic.co
    helm search repo elastic/logstash
    helm pull elastic/logstash --version 7.17.3
    tar -xvzf logstash-7.17.3.tgz
    cd logstash
    edit file values.yaml
    helm upgrade -i insall logtash . -n kube-logging
    
    
    helm pull elastic/filebeat --version 7.17.3
    tar xvzf filebeat-7.17.3.tgz
    cd filebeat
    edit file values.yaml
    helm upgrade -i filebeat . -n kube-logging
