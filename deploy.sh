#!/bin/bash

# Variables - CAMBIAR ESTOS VALORES
RESOURCE_GROUP="heartrate-api-rg"
LOCATION="eastus"
CONTAINER_APP_ENV="heartrate-env"
CONTAINER_APP_NAME="heartrate-api"
CONTAINER_REGISTRY="heartrateregistry$(date +%s)"  # Nombre único
IMAGE_NAME="heartrate-api"

echo "🚀 Desplegando Heart Rate API en Azure Container Apps..."

# 1. Login a Azure (si no estás logueado)
echo "📝 Verificando login de Azure..."
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Por favor haz login:"
    az login
fi

# 2. Crear Resource Group
echo "📦 Creando Resource Group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION

# 3. Crear Azure Container Registry
echo "🏪 Creando Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_REGISTRY \
    --sku Basic \
    --admin-enabled true

# 4. Construir y subir imagen
echo "🔨 Construyendo imagen Docker..."
az acr build \
    --registry $CONTAINER_REGISTRY \
    --image $IMAGE_NAME:latest \
    .

# 5. Obtener credenciales del registry
echo "🔑 Obteniendo credenciales..."
REGISTRY_SERVER=$(az acr show --name $CONTAINER_REGISTRY --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
REGISTRY_USERNAME=$(az acr credential show --name $CONTAINER_REGISTRY --resource-group $RESOURCE_GROUP --query username --output tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $CONTAINER_REGISTRY --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

# 6. Crear Container Apps Environment
echo "🌍 Creando Container Apps Environment..."
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# 7. Desplegar Container App
echo "🚢 Desplegando Container App..."
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image $REGISTRY_SERVER/$IMAGE_NAME:latest \
    --registry-server $REGISTRY_SERVER \
    --registry-username $REGISTRY_USERNAME \
    --registry-password $REGISTRY_PASSWORD \
    --target-port 8000 \
    --ingress external \
    --min-replicas 0 \
    --max-replicas 2 \
    --cpu 0.25 \
    --memory 0.5Gi

# 8. Obtener URL de la aplicación
echo "🎉 ¡Deployment completado!"
FQDN=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv)

echo ""
echo "✅ Tu API está disponible en: https://$FQDN"
echo ""
echo "📋 Endpoints disponibles:"
echo "   GET  https://$FQDN/heartRateData       - Obtener todos los datos"
echo "   POST https://$FQDN/heartRateData       - Crear nuevo registro"
echo "   GET  https://$FQDN/heartRateData/{id}  - Obtener por ID"
echo "   GET  https://$FQDN/docs                - Documentación Swagger"
echo ""
echo "🧪 Ejemplo de POST:"
echo 'curl -X POST "https://'$FQDN'/heartRateData" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d "{"avgHeartRate": 78, "deviceId": "008aad67e94e2937", "endTime": 1727222770000, "maxHeartRate": 85, "minHeartRate": 72, "recordedAt": 1727222778000, "startTime": 1727222770000, "syncTimestamp": 1727222778000}"'
echo ""