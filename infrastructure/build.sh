#!/bin/bash
region=$1
lambdabucket=$2
stackname=$3
bucket=$4
key=$5

aws --region $region cloudformation package --template-file infrastructure/template.yaml --s3-bucket $lambdabucket --output-template-file infrastructure/package.yaml
aws --region $region cloudformation deploy --template-file infrastructure/package.yaml --stack-name $stackname --capabilities CAPABILITY_IAM --parameter-overrides Bucket=$bucket Key=$key
