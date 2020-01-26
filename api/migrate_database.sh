# Install the cloud_sql_proxy
echo $GCLOUD_SQL_SERVICE_KEY > cloud_proxy.key
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy
sudo mkdir /cloudsql
sudo chmod 777 /cloudsql
./cloud_sql_proxy -dir=/cloudsql -instances=baobab:us-central1:baobab -credential_file=cloud_proxy.key & # Run the cloud_sql_proxy
# Run the migrations
cd api
pip install -r requirements.txt
DATABASE_URL=$STAGING_DB_PROXY python run.py db upgrade # Temporarily update the database url to the proxy and run migrations
