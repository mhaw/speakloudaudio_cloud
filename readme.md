how to update: 

1) build: 

build -t gcr.io/speakloudaudio/speakloudaudio_cloud:latest .

2) push

docker push gcr.io/speakloudaudio/speakloudaudio_cloud:latest

3) deploy

gcloud run deploy speakloudaudio-service   --image gcr.io/speakloudaudio/speakloudaudio_cloud:latest   --platform managed   --region us-east1   --allow-unauthenticated   --service-account=speakloudaudio-cloud-admin@speakloudaudio.iam.gserviceaccount.com   --memory=512Mi   --timeout=300s