if [ -f ~/.aws/credentials ]; then
    export AWS_ACCESS_KEY_ID=$(awk '/aws_access_key_id/{print $3}' ~/.aws/credentials)
    export AWS_SECRET_ACCESS_KEY=$(awk '/aws_secret_access_key/{print $3}' ~/.aws/credentials)
fi
