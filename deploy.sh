#!/bin/sh
# Nhan bien moi truong theo dong lenh go vao
if [ $# -ne 4 ]; then
   echo "please specify 2 command line arguments: -f path_of_values.yml -t Tag"
   exit 1
fi

while getopts f:t: flag
do
    case "${flag}" in
        f) filename=${OPTARG};;
        t) tag=${OPTARG};;
        *) echo "Please input -f fullPath_of_values.yaml and -t Release"; exit 1 ;;
    esac
done
# Ham xu ly chuoi YAML
parse_yaml() {
   local prefix=$2
   local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
   sed -ne "s|^\($s\):|\1|" \
        -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
   awk -F$fs '{
      indent = length($1)/2;
      vname[indent] = $2;
      for (i in vname) {if (i > indent) {delete vname[i]}}
      if (length($3) > 0) {
         vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
         printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
      }
   }'
}
#Thuc hien xu ly chuoi trong YAML lay gia tri cac bien
eval $(parse_yaml $filename)

#Bat dau chay Deploy
echo "Deploy Node API App to --Namespace: $namespace --App: $image_repository  --Release: $tag"

deploynamespace=$namespace

#Hieu chinh file tao namespace
newname="name: ${deploynamespace}"
sed -i "s/name:.*/$newname/g" namespace.yaml

#Update TAG version
newtag="tag: ${tag}"
sed -i "s/tag:.*/$newtag/g" $filename

#Create namespace (if not exits) - Helm v.3 and above required Namespace exits  
kubectl apply -f namespace.yaml

#Update Version in Charts
#

#Package Helm
#helm package adetector

#Deploy Helm with namespace
helm upgrade --install adetector ./helm  -n $deploynamespace


# Auto RollBack
#helm upgrade --install --atomic
