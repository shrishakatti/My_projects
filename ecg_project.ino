#include <WiFi.h>
#include <PubSubClient.h>

#define WIFISSID "#enter_name" // WiFi SSID
#define PASSWORD "#enter_pwd" // WiFi Password
#define TOKEN "BBUS-4gxfhirnD3os2hyG33Rmw4qXXXDUbC" // Ubidots Token
#define MQTT_CLIENT_NAME "Joel@1234" // Unique MQTT client name

#define VARIABLE_LABEL "sensor"  // Variable label
#define DEVICE_LABEL "esp32"     // Device label

#define SENSOR 34  // ECG sensor connected to GPIO 34 (supports analog input)

char mqttBroker[] = "industrial.api.ubidots.com"; // Change if needed
char payload[100];
char topic[150];
char str_sensor[10];

WiFiClient ubidots;
PubSubClient client(ubidots);

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received on topic: ");
  Serial.println(topic);
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Attempting MQTT connection...");
    if (client.connect(MQTT_CLIENT_NAME, TOKEN, "")) {
      Serial.println("Connected to Ubidots!");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" Trying again in 2 seconds...");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFISSID, PASSWORD);
  pinMode(SENSOR, INPUT);

  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  client.setServer(mqttBroker, 1883);
  client.setCallback(callback);
}

void sendData() {
  float sensorValue = analogRead(SENSOR);  // Read ECG sensor
  dtostrf(sensorValue, 4, 2, str_sensor);  // Convert to string

  sprintf(topic, "/v1.6/devices/%s", DEVICE_LABEL);
  sprintf(payload, "{\"%s\": {\"value\": %s}}", VARIABLE_LABEL, str_sensor);

  Serial.print("Publishing data: ");
  Serial.println(payload);

  client.publish(topic, payload);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();  // Maintain MQTT connection

  sendData();  // Send ECG data
  delay(5000);  // Wait 5 seconds
}